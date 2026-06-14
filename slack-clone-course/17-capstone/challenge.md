# Challenge 17 — Make It Yours

No reference solution this time — these are open-ended extensions that turn the course
project into *your* project. Pick at least two, build them end-to-end (model → API →
realtime → UI → deployed), and add them to your runbook.

## Build something new

1. **Threaded replies UI.** You already store `parent` and can filter threads (Module
   04). Build the full thread experience: a side panel, reply counts on parent
   messages, and live updates within a thread.

2. **Message edit/delete everywhere.** Wire the consumer events from the Module 05
   challenge into the UI: edit in place, show "(edited)", and tombstone deletes — live
   for all viewers.

3. **Read receipts / "seen by".** Use `ChannelMember.last_read_message_id` to show who
   has read up to which message, updated over the WebSocket.

4. **Slash-command framework.** Generalize `/weather` (Module 08) into a registry of
   commands with help text, argument parsing, and bot responses.

5. **Per-user notification preferences.** Let users choose email vs. in-app per
   workspace/channel, and honor it in the Celery fan-out.

6. **Observability SLOs.** Define SLOs (e.g. 99.9% of message sends < 300ms), build the
   Grafana dashboard and alerts, and run a game-day where you break something and follow
   your own runbook.

## Definition of done (for each feature)

- [ ] Data model + migration, with constraints where appropriate.
- [ ] REST and/or WebSocket API, permission-checked and tenant-scoped.
- [ ] Frontend UI with optimistic/live updates where it makes sense.
- [ ] Tested locally, then deployed to the HA cluster.
- [ ] Documented in your runbook (what it does, how it's wired, how to operate it).

## Ship it

Push your fork, write a README that shows it off (screens + architecture), and you have
a portfolio project that demonstrates real backend, frontend, real-time, async, and
platform skills end-to-end. The native phone app — a separate course — will plug
straight into the API and WebSocket layer you built here.
