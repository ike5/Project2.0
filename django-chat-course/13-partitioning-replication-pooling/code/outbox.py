"""
apps/pulse/chat/outbox.py — the transactional outbox and its Celery relay.

WHAT THIS CLOSES
----------------
Module 09's summary table has one row still marked broken: "persisted to Postgres
but never published." The send path does two writes to two systems:

    await persist(message)                    # commits in Postgres
    await fanout.append(room_key, envelope)   # <-- the worker dies here

The message is durable and will never be delivered. Module 10's resume does not
save you: resume reads the database, so a client that ASKS gets it — but a client
that was connected the whole time never receives it and has NO GAP TO DETECT,
because the seq was allocated and used. It is the only loss mode in Pulse that is
invisible to every other mechanism.

THE SHAPE PULSE ACTUALLY SHIPS
------------------------------
Not "outbox instead of the stream" — that costs 5.2x the send latency (README).

    1. write messages + outbox in ONE transaction   (atomic)
    2. XADD to the stream immediately               (fast path, 1.8 ms)
    3. mark the outbox row published                (best effort)
    4. the relay publishes anything step 2/3 missed (the crash window)

Steady state: the relay finds nothing and costs one indexed query per tick.
After a crash: the relay publishes the handful of rows in the window, the stream
consumer dedups them on (room_id, client_id), and nothing is lost or doubled.
"""

from __future__ import annotations

import json
import logging

from celery import shared_task
from django.db import models, transaction
from django.utils import timezone
from prometheus_client import Counter, Gauge, Histogram

log = logging.getLogger("pulse.outbox")

BATCH = 500          # matches Module 12's measured executemany sweet spot (224k/s)
LOOKBACK_MS = 2000   # do not relay a row younger than this — the fast path is
                     # probably still mid-flight and relaying it just makes a
                     # duplicate the consumer has to absorb.

_relayed = Counter("pulse_outbox_relayed_total", "rows published by the relay")
_skipped = Counter("pulse_outbox_skipped_total", "rows already published by the fast path")
_backlog = Gauge("pulse_outbox_backlog", "unpublished outbox rows")
_lag = Gauge("pulse_outbox_oldest_age_seconds", "age of the oldest unpublished row")
_relay_seconds = Histogram("pulse_outbox_relay_seconds", "one relay tick")


class Outbox(models.Model):
    id = models.BigAutoField(primary_key=True)
    room_id = models.TextField()          # the composed Room.key, e.g. "room.general"
    payload = models.JSONField()          # the full protocol envelope
    created_at = models.DateTimeField(auto_now_add=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "outbox"
        indexes = [
            # PARTIAL, and this matters enormously. The index covers only the
            # BACKLOG — normally a handful of rows — instead of every message
            # ever sent. At 864M rows/day a full index on `id` would be larger
            # than the messages table's primary key and would have to be
            # maintained on every insert to serve a query that returns nothing
            # 99.99% of the time.
            models.Index(fields=["id"], name="idx_outbox_unpublished",
                         condition=models.Q(published_at__isnull=True)),
        ]


# ---------------------------------------------------------------------------
# The write side.
# ---------------------------------------------------------------------------
def persist_with_outbox(*, room_key: str, envelope: dict, sender_id: int) -> int:
    """
    Both rows, one transaction. Called from database_sync_to_async.

    The `messages` insert is raw SQL (Module 12: 41k/s versus the ORM's 7.8k/s on
    the hot path); the outbox insert is the ORM, because it happens once and the
    JSONField adapter is worth having.
    """
    from django.db import connection

    data = envelope["data"]
    with transaction.atomic():
        with connection.cursor() as cur:
            cur.execute(
                """
                INSERT INTO messages
                       (id, room_id, seq, sender, client_id, body, reply_to, created_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, to_timestamp(%s / 1000.0))
                ON CONFLICT (room_id, client_id, created_at) DO NOTHING
                RETURNING id
                """,
                [data["id"], room_key, data["seq"], data["sender"],
                 data["client_id"], data["body"], data.get("reply_to"),
                 envelope["ts"]],
            )
            row = cur.fetchone()
            if row is None:
                # A retry. The message already exists, so there is nothing new to
                # publish — do NOT write an outbox row, or the relay will
                # broadcast a duplicate for a message that was delivered days ago.
                return 0

        Outbox.objects.create(room_id=room_key, payload=envelope)
    return row[0]


def mark_published(outbox_id: int) -> None:
    """Called by the fast path after a successful XADD. Best effort by design."""
    Outbox.objects.filter(pk=outbox_id).update(published_at=timezone.now())


# ---------------------------------------------------------------------------
# The relay.
# ---------------------------------------------------------------------------
@shared_task(name="chat.relay_outbox", bind=True, max_retries=None)
def relay_outbox(self, batch: int = BATCH) -> dict:
    """
    Publish anything the fast path missed.

    SAFE WITH N CONCURRENT RELAY WORKERS because of
    `select_for_update(skip_locked=True)` -> `FOR UPDATE SKIP LOCKED`. Without
    SKIP LOCKED, a second relay worker BLOCKS on the first one's rows and the
    two serialize; with it, the second worker steps over them and takes the next
    500. That one keyword is the difference between a relay that scales and a
    relay that is a single point of throughput.
    """
    from .streams import fanout
    from asgiref.sync import async_to_sync

    cutoff = timezone.now() - timezone.timedelta(milliseconds=LOOKBACK_MS)
    published = 0

    with _relay_seconds.time():
        with transaction.atomic():
            rows = list(
                Outbox.objects
                .select_for_update(skip_locked=True)
                .filter(published_at__isnull=True, created_at__lt=cutoff)
                .order_by("id")[:batch]
            )
            if not rows:
                _report_backlog()
                return {"relayed": 0}

            ids = []
            for row in rows:
                # at-least-once: we may publish and then crash before the UPDATE,
                # producing a duplicate. That is fine and expected — the stream
                # consumer's (room_id, client_id) dedup absorbs it (Module 09).
                # The reverse order (UPDATE then publish) would LOSE messages,
                # which is not fine. Always publish first.
                async_to_sync(fanout.append)(row.room_id, row.payload)
                ids.append(row.id)
                published += 1

            Outbox.objects.filter(id__in=ids).update(published_at=timezone.now())

    _relayed.inc(published)
    _report_backlog()
    log.info("relayed %d outbox rows", published)
    return {"relayed": published}


def _report_backlog() -> None:
    row = (Outbox.objects
           .filter(published_at__isnull=True)
           .aggregate(n=models.Count("id"), oldest=models.Min("created_at")))
    _backlog.set(row["n"] or 0)
    _lag.set((timezone.now() - row["oldest"]).total_seconds() if row["oldest"] else 0.0)


@shared_task(name="chat.vacuum_outbox")
def vacuum_outbox(retain_hours: int = 24) -> int:
    """
    Published rows are dead weight. Delete them, or the partial index's base
    table grows forever and you have reinvented the retention problem this whole
    module exists to solve.

    Deleting in bounded batches, not one big DELETE: a 10-million-row delete
    holds a transaction open long enough to pin every replica's xmin and block
    vacuum database-wide — the exact failure the partitioning section opens with.
    """
    cutoff = timezone.now() - timezone.timedelta(hours=retain_hours)
    total = 0
    while True:
        ids = list(Outbox.objects
                   .filter(published_at__lt=cutoff)
                   .values_list("id", flat=True)[:10_000])
        if not ids:
            return total
        total += Outbox.objects.filter(id__in=ids).delete()[0]


# Celery beat:
#
#   CELERY_BEAT_SCHEDULE = {
#       "relay-outbox": {"task": "chat.relay_outbox", "schedule": 1.0},
#       "vacuum-outbox": {"task": "chat.vacuum_outbox",
#                         "schedule": crontab(minute=23)},
#   }
#
# A 1-second beat is a poll, and polling has a floor on latency. To go instant,
# add `NOTIFY outbox` in a trigger and have one relay worker `LISTEN` — but note
# that LISTEN/NOTIFY is session state and therefore DOES NOT WORK THROUGH
# PGBOUNCER IN TRANSACTION MODE. The listener needs a direct connection to the
# primary, bypassing the pooler. Lab Part E shows the failure and the fix.
#
# ALERT ON pulse_outbox_backlog AND pulse_outbox_oldest_age_seconds, not on the
# task: a relay that has stopped emits nothing to alert on, while the backlog it
# was supposed to drain is a number you can see.
