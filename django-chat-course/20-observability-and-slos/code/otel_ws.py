#!/usr/bin/env python3
"""OpenTelemetry across the WebSocket boundary — reference copy of `chat/tracing.py`.

Every OpenTelemetry integration assumes a request scope: something starts, does
work, and ends, and the SDK's context follows it. A WebSocket connection breaks
all three assumptions at once, and the default ASGI instrumentation handles it
by doing the literal thing -- one span for the whole connection.

This module does four things:

  1. Turns that off for `websocket` scopes and spans each MESSAGE instead.
  2. Injects/extracts W3C traceparent across the channel layer, the Redis
     Stream, the outbox row and the Celery task -- the four hops where a
     Python context does not survive.
  3. Puts `pulse.worker` on every span, which is what makes an event-loop stall
     diagnosable at all (see loop_watchdog.py).
  4. Keeps the span count proportional to MESSAGES, not to recipients.

Setup, in `pulse/asgi.py`, before the app is built:

    from chat.tracing import configure_tracing, TracedProtocolTypeRouter
    configure_tracing()
"""

from __future__ import annotations

import os
from typing import Any

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from opentelemetry.sdk.trace.sampling import ALWAYS_ON
from opentelemetry.trace import SpanKind, Status, StatusCode
from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

WORKER = os.environ.get("PULSE_WORKER") or f"pid-{os.getpid()}"
POD = os.environ.get("PULSE_POD", "local")
REGION = os.environ.get("PULSE_REGION", "us")

_propagator = TraceContextTextMapPropagator()
tracer = trace.get_tracer("pulse.chat")


def configure_tracing() -> None:
    """Build the provider. Called once per WORKER PROCESS, not once per pod."""
    resource = Resource.create({
        "service.name": "pulse",
        "service.version": os.environ.get("PULSE_VERSION", "dev"),
        # These three are the difference between a usable trace store and a
        # pile of spans. `pulse.worker` in particular: in a process-per-core
        # runtime the worker is the failure domain, and a span that cannot name
        # its worker cannot be correlated with the stall that delayed it.
        "pulse.worker": WORKER,
        "pulse.pod": POD,
        "pulse.region": REGION,
    })

    provider = TracerProvider(
        resource=resource,
        # ALWAYS_ON. Head sampling here is the mistake this module exists to
        # prevent: at 1% you throw away 99% of your ERRORS along with 99% of
        # everything else. The collector tail-samples instead, keeping 100% of
        # slow and failed traces (infra/obs/otel-collector.yaml).
        #
        # The cost is real -- ~6,000 spans/s leave each app node at the knee --
        # which is why the exporter below is tuned rather than left at defaults.
        sampler=ALWAYS_ON,
    )
    provider.add_span_processor(BatchSpanProcessor(
        OTLPSpanExporter(endpoint=os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT",
                                                 "http://otel-collector:4317"),
                         insecure=True),
        # Defaults are 512/2048/5000ms, which at 6,000 spans/s drops spans and
        # logs "Queue is full" once, at startup, and never again.
        max_queue_size=16384,
        max_export_batch_size=1024,
        schedule_delay_millis=2000,
    ))
    trace.set_tracer_provider(provider)


# ---------------------------------------------------------------------------
# 1. Do NOT let the ASGI instrumentation span the connection.
# ---------------------------------------------------------------------------
def excluded_urls_for_asgi() -> str:
    """Instrument HTTP, not WebSocket.

    `OpenTelemetryMiddleware` opens a server span when a scope begins and ends
    it when the scope ends. For `http` that is a request; for `websocket` it is
    the whole connection, which for Pulse means up to six hours. Three failures
    follow, and the lab measures all three before fixing them:

      - BatchSpanProcessor exports on span END, so nothing is visible for the
        life of the connection.
      - The SDK's default max_events_per_span is 128. A busy socket produces
        thousands of receive/send events and the rest are silently dropped.
      - A trace containing 40,000 messages from one user is a trace of nothing.

    Also exclude the scrape and probe endpoints: /metrics is hit every 15 s by
    Prometheus and /healthz every 3 s by the kubelet, and neither is work.
    """
    return "healthz,readyz,metrics"


def should_trace_scope(scope: dict) -> bool:
    return scope.get("type") == "http" and not any(
        scope.get("path", "").endswith(p) for p in ("/healthz", "/readyz", "/metrics")
    )


# ---------------------------------------------------------------------------
# 2. The four hops where context does not survive.
# ---------------------------------------------------------------------------
def inject(carrier: dict[str, str] | None = None) -> dict[str, str]:
    """Serialise the current trace context into a plain dict.

    Put the result in: the channel-layer event dict, the Redis Stream entry's
    fields, the outbox row's `trace_context` jsonb column, and the Celery task's
    headers. All four are network messages, and a contextvar is not.

    What you do NOT need to do this for: `asyncio.create_task` (the new task
    copies the current context) and `database_sync_to_async` (asgiref copies the
    context across the threadpool boundary). Those two work, and knowing they
    work saves you from wrapping everything defensively.
    """
    carrier = {} if carrier is None else carrier
    _propagator.inject(carrier)
    return carrier


def extract(carrier: dict[str, Any] | None):
    """Restore a context injected by `inject`. Missing/garbage carrier -> a new
    root context, never an exception -- an unparseable traceparent must not be
    able to drop a message."""
    try:
        return _propagator.extract(carrier or {})
    except Exception:
        return None


# ---------------------------------------------------------------------------
# 3. Per-message spans.
# ---------------------------------------------------------------------------
def send_span(room_key: str, client_id: str):
    """The inbound half: a client's message.create arrives on this worker.

    `room_key` is Module 05's wire identifier (`room.7`), NOT the bare slug and
    NOT the Redis key. Using one identifier everywhere in telemetry is the only
    way a TraceQL query and a log query can be written by the same person.
    """
    return tracer.start_as_current_span(
        "chat.send",
        kind=SpanKind.SERVER,
        attributes={
            "chat.room": room_key,
            # client_id is high-cardinality and that is FINE here: traces are
            # indexed per-span, not aggregated into series. This is exactly the
            # per-entity detail the README says belongs in traces, not metrics.
            "chat.client_id": client_id,
            "pulse.worker": WORKER,
        },
    )


def fanout_span(room_key: str, recipients: int, carrier: dict[str, Any] | None):
    """The outbound half, on a DIFFERENT worker in a DIFFERENT pod.

    ONE span for the whole fan-out, with the recipient count as an attribute. A
    span per recipient is 199x the trace volume for information
    chat_delivery_recipient_latency_seconds already gives you, aggregated
    correctly, for free.
    """
    from chat.delivery_metrics import bucket
    return tracer.start_as_current_span(
        "chat.fanout",
        context=extract(carrier),
        kind=SpanKind.CONSUMER,
        attributes={
            "chat.room": room_key,
            "chat.recipients": recipients,
            "chat.room_size_bucket": bucket(recipients),
            "pulse.worker": WORKER,
        },
    )


# ---------------------------------------------------------------------------
# 4. The consumer mixin that wires it all together.
# ---------------------------------------------------------------------------
class TracedConsumerMixin:
    """Mix into `ChatConsumer` above `AsyncJsonWebsocketConsumer`.

    Note what is NOT here: a span for `connect` that stays open. `connect` gets
    its own short span and ends. The connection's LIFETIME is a gauge
    (`chat_connections_active`), not a span, because a six-hour span is a
    six-hour blind spot.
    """

    async def connect(self):
        with tracer.start_as_current_span(
            "chat.connect",
            kind=SpanKind.SERVER,
            attributes={"chat.room": self.room.key, "pulse.worker": WORKER},
        ) as span:
            try:
                await super().connect()
                span.set_attribute("chat.outcome", "accepted")
            except Exception as exc:
                span.set_status(Status(StatusCode.ERROR, str(exc)))
                raise

    async def receive_json(self, content, **kwargs):
        mtype = content.get("type", "unknown")
        # Typing indicators and pings are 80% of inbound frames and 0% of the
        # interesting ones. Spanning them triples your volume to trace a no-op.
        if mtype in ("ping", "typing.start"):
            return await super().receive_json(content, **kwargs)

        with tracer.start_as_current_span(
            f"chat.{mtype}",
            kind=SpanKind.SERVER,
            attributes={"chat.room": self.room.key, "pulse.worker": WORKER},
        ) as span:
            try:
                return await super().receive_json(content, **kwargs)
            except Exception as exc:
                span.set_status(Status(StatusCode.ERROR, type(exc).__name__))
                raise

    async def group_send_traced(self, event: dict) -> None:
        """group_send with the traceparent riding along in the event dict."""
        event["_trace"] = inject()
        await self.channel_layer.group_send(self.room.key, event)

    async def chat_message(self, event: dict) -> None:
        """The channel-layer handler. Restores the context the sender injected."""
        recipients = len(getattr(self, "_room_local_sockets", ()) or (1,))
        with fanout_span(self.room.key, recipients, event.get("_trace")):
            await super().chat_message(event)
