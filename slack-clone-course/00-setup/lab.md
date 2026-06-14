# Lab 00 — Prove Your Environment Works

**You'll:** start the local data services, connect to Postgres and Redis by hand,
peek at the mail and storage UIs, then create and verify your Kubernetes cluster.

⏱️ ~30 min. Run commands from `slack-clone-course/00-setup` unless noted.

---

## Part A — Bring up the data services

```bash
cd 00-setup
chmod +x scripts/*.sh               # make the helper scripts executable (once)
docker compose -f compose.dev.yml up -d
docker compose -f compose.dev.yml ps
```

✅ Expected: `postgres`, `redis`, `mailhog`, `minio` all `running` (Postgres,
Redis, MinIO show `healthy` after a few seconds).

---

## Part B — Talk to Postgres

Connect with `psql` *inside* the container (no local client needed):

```bash
docker compose -f compose.dev.yml exec postgres psql -U slack -d slack
```
Inside the prompt:
```sql
SELECT version();      -- PostgreSQL 16.x ...
\l                     -- list databases (you'll see "slack")
\q                     -- quit
```

✅ **Checkpoint:** you reached Postgres 16 with the `slack` user and database that
later modules' settings expect.

---

## Part C — Talk to Redis

```bash
docker compose -f compose.dev.yml exec redis redis-cli
```
Inside the prompt:
```
PING            -> PONG
SET hello world -> OK
GET hello       -> "world"
TTL hello       -> -1        (no expiry yet)
EXPIRE hello 30 -> 1         (this is how presence keys auto-expire later)
TTL hello       -> ~30
exit
```

✅ **Checkpoint:** Redis answers `PONG` and you set/read a key with a TTL — the
exact mechanism Module 06 uses for presence.

---

## Part D — Mail and storage dashboards

These back email (Module 07) and uploads (Module 11). Just confirm they load:

- Open <http://localhost:8025> → the **MailHog** inbox (empty for now).
- Open <http://localhost:9001> → the **MinIO** console; log in with
  `minioadmin` / `minioadmin`.

✅ **Checkpoint:** both UIs open. You don't need to do anything in them yet.

---

## Part E — Create and verify the Kubernetes cluster

```bash
./scripts/create-cluster.sh        # ~1 min the first time
./scripts/verify-setup.sh
```

✅ Expected: 3 nodes `Ready`:
```
slack-control-plane   Ready   control-plane
slack-worker          Ready   <none>
slack-worker2         Ready   <none>
```

Look around:
```bash
kubectl get nodes -o wide
kubectl get pods -A           # the cluster's own system pods, all Running
```

Now free your laptop — you don't need the cluster again until Module 13:
```bash
./scripts/delete-cluster.sh
```

> Leave the **data services** (`compose.dev.yml`) running — Module 02 uses them
> immediately. Only the kind cluster gets torn down here.

---

## What you learned
- The app depends on Postgres, Redis, MailHog, and MinIO — all run locally in containers.
- You can reach Postgres with `psql` and Redis with `redis-cli` for debugging.
- Redis keys can carry a TTL — the basis for presence and rate limiting later.
- Your kind cluster is disposable: create it in ~1 minute, delete it to reclaim RAM.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 01](../01-architecture-domain/).
