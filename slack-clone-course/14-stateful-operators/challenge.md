# Challenge 14 — Trust the Data Tier

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Scheduled backups.** Configure CloudNativePG to stream backups to MinIO and add a
   `ScheduledBackup` (e.g. nightly). Trigger an on-demand `Backup` and confirm objects
   land in the bucket.

2. **Failover keeps writes flowing.** Run a loop that POSTs a message every second.
   Delete the Postgres primary mid-loop and measure how many requests fail and for how
   long before writes resume against the promoted primary.

3. **Read/write split (discussion + try).** Point a read-only report query at
   `slack-pg-ro`. Explain which of the app's queries could safely use replicas and why
   most chat reads should still hit the primary (replication lag vs. read-your-writes).

4. **Redis failover.** Delete the Redis master pod while two browsers are chatting.
   Observe whether messages resume after Sentinel promotes a new master, and note any
   blip in real-time delivery.

5. **Stretch:** HA and backups protect against different things. Give a concrete
   incident each one saves you from, and one incident where you'd need **both**.

## Success criteria
- [ ] Scheduled + on-demand backups land in object storage.
- [ ] You measured the write outage window during Postgres failover.
- [ ] You can reason about routing reads to replicas vs. the primary.
- [ ] Real-time messaging recovers after a Redis master failover.
- [ ] You can distinguish what HA vs. backups protect against.
