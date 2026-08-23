# Lab 04 — A Chat That Works (On One Node)

**You'll:** wire STOMP, build room-scoped chat with presence, test it from a
browser and from `websocat`, tune the channels, and then **prove the simple
broker can't span two instances**.

⏱️ ~90 min. Work in `spring-boot-chat-course/apps/pulse`.

---

## Part A — STOMP configuration

`src/main/java/com/pulse/ws/WebSocketConfig.java`:

```java
package com.pulse.ws;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.messaging.simp.config.ChannelRegistration;
import org.springframework.messaging.simp.config.MessageBrokerRegistry;
import org.springframework.scheduling.concurrent.ThreadPoolTaskScheduler;
import org.springframework.web.socket.config.annotation.*;

@Configuration
@EnableWebSocketMessageBroker
public class WebSocketConfig implements WebSocketMessageBrokerConfigurer {

    private final AuthChannelInterceptor authInterceptor;

    public WebSocketConfig(AuthChannelInterceptor authInterceptor) {
        this.authInterceptor = authInterceptor;
    }

    @Override
    public void registerStompEndpoints(StompEndpointRegistry registry) {
        registry.addEndpoint("/ws")
                .setAllowedOriginPatterns("http://localhost:*");   // NOT "*" — see Module 21
    }

    @Override
    public void configureMessageBroker(MessageBrokerRegistry registry) {
        registry.enableSimpleBroker("/topic", "/queue")
                .setHeartbeatValue(new long[]{10_000, 10_000})
                .setTaskScheduler(heartbeatScheduler());   // REQUIRED or heartbeats do nothing

        registry.setApplicationDestinationPrefixes("/app");
        registry.setUserDestinationPrefix("/user");
    }

    @Override
    public void configureClientInboundChannel(ChannelRegistration registration) {
        registration.interceptors(authInterceptor);
        registration.taskExecutor()
                .corePoolSize(16)
                .maxPoolSize(32)
                .queueCapacity(1_000);        // BOUNDED. The default is unbounded.
    }

    @Override
    public void configureClientOutboundChannel(ChannelRegistration registration) {
        registration.taskExecutor()
                .corePoolSize(16)
                .maxPoolSize(64)              // fan-out lands here — more headroom
                .queueCapacity(10_000);
    }

    @Override
    public void configureWebSocketTransport(WebSocketTransportRegistration registration) {
        registration.setMessageSizeLimit(64 * 1024)
                    .setSendBufferSizeLimit(512 * 1024)   // slow-consumer protection
                    .setSendTimeLimit(20 * 1000);
    }

    @Bean
    public ThreadPoolTaskScheduler heartbeatScheduler() {
        var scheduler = new ThreadPoolTaskScheduler();
        scheduler.setPoolSize(1);
        scheduler.setThreadNamePrefix("stomp-heartbeat-");
        scheduler.initialize();
        return scheduler;
    }
}
```

---

## Part B — Authentication interceptor

For now, a trivially fake token (`user:alice`). Module 21 replaces it with real
JWT verification.

`src/main/java/com/pulse/ws/AuthChannelInterceptor.java`:

```java
package com.pulse.ws;

import org.springframework.messaging.Message;
import org.springframework.messaging.MessageChannel;
import org.springframework.messaging.simp.stomp.StompCommand;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.messaging.support.ChannelInterceptor;
import org.springframework.messaging.support.MessageHeaderAccessor;
import org.springframework.stereotype.Component;

import java.security.Principal;

@Component
public class AuthChannelInterceptor implements ChannelInterceptor {

    record ChatPrincipal(String name) implements Principal {
        @Override public String getName() { return name; }
    }

    @Override
    public Message<?> preSend(Message<?> message, MessageChannel channel) {
        StompHeaderAccessor accessor =
                MessageHeaderAccessor.getAccessor(message, StompHeaderAccessor.class);
        if (accessor == null) return message;

        if (StompCommand.CONNECT.equals(accessor.getCommand())) {
            String token = accessor.getFirstNativeHeader("Authorization");
            if (token == null || !token.startsWith("user:")) {
                throw new IllegalArgumentException("missing or malformed Authorization header");
            }
            // Attaching the principal to the ACCESSOR attaches it to the SESSION,
            // so every subsequent frame on this socket carries it.
            accessor.setUser(new ChatPrincipal(token.substring("user:".length())));
        }
        return message;
    }
}
```

> Throwing from `preSend` on a `CONNECT` causes Spring to send a STOMP `ERROR`
> frame and close the socket. That's the behaviour you want — the client learns
> *why*, unlike a bare TCP close.

---

## Part C — The chat controller

`src/main/java/com/pulse/chat/ChatController.java`:

```java
package com.pulse.chat;

import org.springframework.messaging.handler.annotation.*;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.stereotype.Controller;

import java.security.Principal;
import java.time.Instant;
import java.util.UUID;

@Controller
public class ChatController {

    public record Inbound(String clientId, String body) {}
    public record Outbound(String id, String clientId, String roomId,
                           String sender, String body, long ts) {}

    private final SimpMessagingTemplate template;

    public ChatController(SimpMessagingTemplate template) {
        this.template = template;
    }

    /**
     * Clients SEND to /app/room.{roomId}/send.
     * Note they never publish to /topic directly — that would bypass this method
     * and with it every validation, persistence and rate-limit hook we'll add later.
     */
    @MessageMapping("/room.{roomId}/send")
    public void send(@DestinationVariable String roomId,
                     @Payload Inbound inbound,
                     Principal principal) {

        var out = new Outbound(
                UUID.randomUUID().toString(),
                inbound.clientId(),                    // echoed so the sender can dedup
                roomId,
                principal.getName(),
                inbound.body(),
                Instant.now().toEpochMilli());

        template.convertAndSend("/topic/room." + roomId, out);

        // Private receipt to the sender only: "I have your message, here's its id".
        // Module 10 turns this into a real ack protocol.
        template.convertAndSendToUser(principal.getName(), "/queue/receipts",
                new Receipt(inbound.clientId(), out.id(), out.ts()));
    }

    public record Receipt(String clientId, String messageId, long ts) {}
}
```

---

## Part D — Presence via session events

Spring publishes application events for the STOMP lifecycle. Wire the
`SessionRegistry` from Module 01's challenge into them.

`src/main/java/com/pulse/chat/PresenceListener.java`:

```java
package com.pulse.chat;

import com.pulse.registry.SessionRegistry;
import org.springframework.context.event.EventListener;
import org.springframework.messaging.simp.SimpMessagingTemplate;
import org.springframework.messaging.simp.stomp.StompHeaderAccessor;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.messaging.*;

@Component
public class PresenceListener {

    private final SessionRegistry registry;
    private final SimpMessagingTemplate template;

    public PresenceListener(SessionRegistry registry, SimpMessagingTemplate template) {
        this.registry = registry;
        this.template = template;
    }

    public record Presence(String user, String state, long ts) {}

    @EventListener
    public void onConnected(SessionConnectedEvent event) {
        var accessor = StompHeaderAccessor.wrap(event.getMessage());
        if (accessor.getUser() == null) return;
        registry.connect(accessor.getSessionId(), accessor.getUser().getName());
    }

    @EventListener
    public void onSubscribe(SessionSubscribeEvent event) {
        var accessor = StompHeaderAccessor.wrap(event.getMessage());
        String destination = accessor.getDestination();
        if (destination == null || !destination.startsWith("/topic/room.")) return;

        String roomId = destination.substring("/topic/room.".length());
        registry.subscribe(accessor.getSessionId(), roomId);

        template.convertAndSend("/topic/room." + roomId + ".presence",
                new Presence(accessor.getUser().getName(), "joined", System.currentTimeMillis()));
    }

    @EventListener
    public void onDisconnect(SessionDisconnectEvent event) {
        var accessor = StompHeaderAccessor.wrap(event.getMessage());
        String sessionId = accessor.getSessionId();

        // Capture rooms BEFORE disconnect() clears them, or you can't announce the exit.
        var rooms = registry.roomsFor(sessionId);
        String user = accessor.getUser() != null ? accessor.getUser().getName() : "unknown";

        rooms.forEach(roomId -> template.convertAndSend("/topic/room." + roomId + ".presence",
                new Presence(user, "left", System.currentTimeMillis())));

        registry.disconnect(sessionId);
    }
}
```

> ⚠️ The ordering in `onDisconnect` matters. Call `registry.disconnect()` first
> and `roomsFor()` returns empty — you'd never announce the departure. This is a
> real bug people ship.

---

## Part E — Run it and talk to it by hand

```bash
./mvnw spring-boot:run
```

**Expected in the log:**
```
Starting...
Started PulseApplication in 2.4 seconds
```

Talk STOMP by hand. STOMP frames end with a NUL byte, so use `websocat`'s
text mode with an explicit terminator — the helper script does the escaping:

`code/stomp.sh`:
```bash
#!/usr/bin/env bash
# Minimal STOMP-over-WebSocket client.
#   ./stomp.sh alice room.7
USER="${1:-alice}"; ROOM="${2:-room.7}"
NUL=$'\x00'
{
  printf 'CONNECT\naccept-version:1.2\nheart-beat:10000,10000\nAuthorization:user:%s\n\n%s\n' "$USER" "$NUL"
  sleep 0.5
  printf 'SUBSCRIBE\nid:sub-0\ndestination:/topic/%s\n\n%s\n' "$ROOM" "$NUL"
  printf 'SUBSCRIBE\nid:sub-1\ndestination:/user/queue/receipts\n\n%s\n' "$NUL"
  while IFS= read -r line; do
    printf 'SEND\ndestination:/app/%s/send\ncontent-type:application/json\n\n{"clientId":"c-%s","body":"%s"}%s\n' \
      "$ROOM" "$RANDOM" "$line" "$NUL"
  done
} | websocat -n --text ws://localhost:8080/ws
```

```bash
chmod +x code/stomp.sh
./code/stomp.sh alice room.7
```

**Expected** — the `CONNECTED` frame, then your own message echoed back plus a
receipt:
```
CONNECTED
version:1.2
heart-beat:10000,10000
user-name:alice
```
Type `hello` and press Enter:
```
MESSAGE
destination:/topic/room.7
subscription:sub-0
message-id:abc-3
content-type:application/json

{"id":"9f3c...","clientId":"c-18342","roomId":"room.7","sender":"alice","body":"hello","ts":1735689600123}

MESSAGE
destination:/user/queue/receipts
subscription:sub-1

{"clientId":"c-18342","messageId":"9f3c...","ts":1735689600123}
```

✅ Note `user-name:alice` in the `CONNECTED` frame — that's your interceptor's
principal, echoed back. And note the receipt arrived on
`/user/queue/receipts` even though the server sent to
`convertAndSendToUser("alice", "/queue/receipts", ...)`. Spring rewrote the
destination per-session.

**Now prove the auth works.** Remove the `Authorization` line from the CONNECT
frame:

```bash
printf 'CONNECT\naccept-version:1.2\n\n\x00\n' | websocat -n --text ws://localhost:8080/ws
```

**Expected:**
```
ERROR
message:Failed to send message to ExecutorSubscribableChannel
content-type:text/plain

java.lang.IllegalArgumentException: missing or malformed Authorization header
```

✅ A STOMP `ERROR` frame, then the socket closes. The client knows *why*.

---

## Part F — Two clients, one room

Open two terminals:

```bash
./code/stomp.sh alice room.7     # terminal 1
./code/stomp.sh bob   room.7     # terminal 2
```

Also subscribe to presence — add this to a third terminal:
```bash
printf 'CONNECT\naccept-version:1.2\nAuthorization:user:watcher\n\n\x00\nSUBSCRIBE\nid:p\ndestination:/topic/room.7.presence\n\n\x00\n' \
  | websocat -n --text ws://localhost:8080/ws
```

Type in alice's terminal. **Expected in bob's terminal:**
```
MESSAGE
destination:/topic/room.7
subscription:sub-0

{"id":"...","sender":"alice","body":"hi bob","ts":...}
```

**Expected in the watcher terminal** when bob connected:
```
MESSAGE
destination:/topic/room.7.presence

{"user":"bob","state":"joined","ts":1735689600123}
```

Now Ctrl-C bob. **Expected in the watcher:**
```
{"user":"bob","state":"left","ts":1735689612456}
```

✅ You have chat.

---

## Part G — A browser client

`src/main/resources/static/index.html`:

```html
<!doctype html>
<meta charset="utf-8">
<title>Pulse</title>
<style>
  body { font: 14px/1.5 system-ui, sans-serif; max-width: 620px; margin: 2rem auto; }
  #log { border: 1px solid #ccc; height: 340px; overflow-y: auto; padding: .5rem; }
  .me { color: #06c; } .sys { color: #888; font-style: italic; }
  input, button { font: inherit; padding: .35rem; }
</style>

<h1>Pulse</h1>
<p>user <input id="user" value="alice"> room <input id="room" value="room.7">
   <button id="go">connect</button> <span id="state" class="sys">disconnected</span></p>
<div id="log"></div>
<p><input id="msg" size="50" placeholder="type and press enter" disabled></p>

<script type="module">
import { Client } from 'https://cdn.jsdelivr.net/npm/@stomp/stompjs@7/+esm';

const log = (text, cls = '') => {
  const div = document.createElement('div');
  div.className = cls; div.textContent = text;
  document.getElementById('log').append(div);
  div.scrollIntoView();
};

let client;
document.getElementById('go').onclick = () => {
  const user = document.getElementById('user').value;
  const room = document.getElementById('room').value;

  client = new Client({
    brokerURL: 'ws://localhost:8080/ws',
    connectHeaders: { Authorization: 'user:' + user },
    heartbeatIncoming: 10000,
    heartbeatOutgoing: 10000,
    reconnectDelay: 0,          // deliberately OFF — Module 17 does this properly
    onConnect: () => {
      document.getElementById('state').textContent = 'connected';
      document.getElementById('msg').disabled = false;

      client.subscribe('/topic/' + room, f => {
        const m = JSON.parse(f.body);
        log(`${m.sender}: ${m.body}`, m.sender === user ? 'me' : '');
      });
      client.subscribe('/topic/' + room + '.presence', f => {
        const p = JSON.parse(f.body);
        log(`— ${p.user} ${p.state}`, 'sys');
      });
      client.subscribe('/user/queue/receipts', f => {
        const r = JSON.parse(f.body);
        log(`  ✓ ${r.clientId} → ${r.messageId}`, 'sys');
      });
    },
    onStompError: f => log('ERROR: ' + f.headers.message, 'sys'),
    onWebSocketClose: e => {
      document.getElementById('state').textContent = `closed (${e.code})`;
      log(`socket closed, code=${e.code}`, 'sys');
    },
  });
  client.activate();
};

document.getElementById('msg').addEventListener('keydown', e => {
  if (e.key !== 'Enter' || !e.target.value) return;
  client.publish({
    destination: '/app/' + document.getElementById('room').value + '/send',
    body: JSON.stringify({ clientId: 'c-' + crypto.randomUUID(), body: e.target.value }),
  });
  e.target.value = '';
});
</script>
```

```bash
open http://localhost:8080/index.html      # or xdg-open / just paste it
```

Open **two browser tabs**, use different usernames, join the same room.

**Expected:** messages appear in both tabs; presence lines announce joins and
leaves; the sender sees a `✓` receipt line.

✅ Open DevTools → Network → WS → Messages to watch the actual STOMP frames.
That view is worth ten minutes of staring — you'll see the heartbeat newlines
ticking every 10 seconds.

---

## Part H — Watch the heartbeats and prove they matter

In DevTools' WS Messages panel you should see tiny frames every 10 s containing
just a newline. **Confirm they're real** — set `heartbeatOutgoing: 0` in the
browser client, reconnect, and watch the server:

```bash
curl -s localhost:8080/actuator/metrics/jvm.threads.live | jq '.measurements[0].value'
```

Then close the laptop lid / disable Wi-Fi for 60 seconds and re-check. With
heartbeats **off**, the session lingers. With them **on**, the server notices and
fires `SessionDisconnectEvent`.

**Expected with heartbeats on**, after ~20–30 s of a dead client:
```
Session closed, no heartbeat received from client within 20000 ms
```

✅ That log line is your file descriptor being reclaimed. Without it you leak one
per abandoned connection, forever.

---

## Part I — The wall: two instances can't see each other

This is the point of the entire module.

```bash
# terminal 1
SERVER_PORT=8080 ./mvnw spring-boot:run
# terminal 2
SERVER_PORT=8081 ./mvnw spring-boot:run
```

Connect alice to **8080** and bob to **8081**, both to `room.7`:

```bash
# terminal 3
./code/stomp.sh alice room.7                                   # hits 8080
# terminal 4  (edit stomp.sh's URL, or:)
sed 's/8080/8081/' code/stomp.sh > /tmp/stomp8081.sh && chmod +x /tmp/stomp8081.sh
/tmp/stomp8081.sh bob room.7
```

Type in alice's terminal.

**Expected — and this is the whole lesson:**
```
(alice sees her own message echoed)
(bob sees NOTHING)
```

✅ **Nothing is broken.** Both servers work perfectly. Instance 8080's
`SimpleBrokerMessageHandler` has a `ConcurrentHashMap` containing alice's
subscription. Instance 8081 has one containing bob's. Neither map knows the
other exists, and there is no code path between two JVMs' heaps.

Confirm it with the registry endpoint:
```bash
curl -s localhost:8080/rooms/room.7/sessions | jq
curl -s localhost:8081/rooms/room.7/sessions | jq
```
**Expected:**
```json
["4b1e7c39"]
["9a2f0d51"]
```

Two servers, two disjoint views of the same logical room.

**This is Problem 2 from Module 00 — fan-out — arriving in person.** Everything
in Phase 2 exists to put a shared backbone between these two maps.

---

## Part J — Tune and observe the channels

Add channel metrics so Module 06 has something to graph.

`src/main/java/com/pulse/ws/ChannelMetrics.java`:

```java
package com.pulse.ws;

import io.micrometer.core.instrument.Gauge;
import io.micrometer.core.instrument.MeterRegistry;
import jakarta.annotation.PostConstruct;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.scheduling.concurrent.ThreadPoolTaskExecutor;
import org.springframework.stereotype.Component;

@Component
public class ChannelMetrics {

    private final MeterRegistry registry;
    private final ThreadPoolTaskExecutor inbound;
    private final ThreadPoolTaskExecutor outbound;

    public ChannelMetrics(MeterRegistry registry,
                          @Qualifier("clientInboundChannelExecutor")  ThreadPoolTaskExecutor inbound,
                          @Qualifier("clientOutboundChannelExecutor") ThreadPoolTaskExecutor outbound) {
        this.registry = registry;
        this.inbound = inbound;
        this.outbound = outbound;
    }

    @PostConstruct
    void bind() {
        bindOne("inbound", inbound);
        bindOne("outbound", outbound);
    }

    private void bindOne(String name, ThreadPoolTaskExecutor executor) {
        Gauge.builder("stomp.channel.active", executor, ThreadPoolTaskExecutor::getActiveCount)
             .tag("channel", name).register(registry);
        Gauge.builder("stomp.channel.queued", executor,
                      e -> e.getThreadPoolExecutor().getQueue().size())
             .tag("channel", name).register(registry);
        Gauge.builder("stomp.channel.pool.size", executor, ThreadPoolTaskExecutor::getPoolSize)
             .tag("channel", name).register(registry);
    }
}
```

```bash
curl -s localhost:8080/actuator/metrics/stomp.channel.queued | jq
watch -n1 'curl -s localhost:8080/actuator/prometheus | grep stomp_channel'
```

**Expected at idle:**
```
stomp_channel_active{channel="inbound",...} 0.0
stomp_channel_queued{channel="inbound",...} 0.0
stomp_channel_active{channel="outbound",...} 0.0
stomp_channel_queued{channel="outbound",...} 0.0
```

✅ Those queue gauges are the ones that climb before your server falls over in
Module 06. Watching them go non-zero is your early warning.

---

## What you built

- A real chat server: rooms, presence, receipts, authentication, heartbeats.
- A browser client and a shell client, both speaking real STOMP.
- Bounded channel queues and slow-consumer limits — **not** the defaults.
- Metrics on the two queues that predict overload.
- **A demonstrated, understood wall:** two instances cannot share a room.

Now do [`challenge.md`](./challenge.md).

Then: [Module 05 — Protocol & Domain Design](../05-protocol-and-domain-design/).
