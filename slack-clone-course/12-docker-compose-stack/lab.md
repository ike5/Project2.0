# Lab 12 — The Whole App in Containers

**You'll:** build the backend and frontend images, run the full stack with one
command, and verify every feature works end-to-end inside containers.

⏱️ ~50 min. Docker installed. Stop the dev `compose.dev.yml` and any local
`runserver`/`npm run dev` first (to free the ports).

---

## Part A — Inspect the images

Read both Dockerfiles:
```bash
cat apps/slack-backend/Dockerfile      # multi-stage, non-root, role entrypoint
cat apps/slack-backend/entrypoint.sh   # web | worker | beat | migrate
cat apps/slack-frontend/Dockerfile     # standalone Next output
```
✅ **Checkpoint:** you can point to the builder vs runtime stages and the role switch.

---

## Part B — Bring it all up

```bash
cd slack-clone-course
docker compose up --build
```
Watch the boot order: postgres/redis become healthy, `web` runs migrations
(`RUN_MIGRATIONS=1`) then serves, `worker` and `beat` connect, `frontend` builds and
starts.

✅ Expected: all seven services running; no crash loops.

In another terminal:
```bash
docker compose ps
curl -s localhost:8000/api/health/    # {"status":"ok"}
```

---

## Part C — Create an admin and a workspace

```bash
docker compose exec web python manage.py createsuperuser
```
Open <http://localhost:8000/admin/>, create a workspace, a channel, and add your user.

---

## Part D — Use the app end-to-end

Open <http://localhost:3000>:
- Register / log in.
- Send messages in a channel — they appear live (WebSockets through the `web` container).
- Open a second browser as another member and chat between them.
- @mention an offline user → check **MailHog** (<http://localhost:8025>) for the
  email (sent by the `worker` container).
- Attach a file → it lands in **MinIO** (<http://localhost:9001>).

✅ **Checkpoint:** every subsystem (DRF, Channels, Celery, storage) works composed.

---

## Part E — Prove the worker is separate

```bash
docker compose logs -f worker      # watch fan_out_message / send_email run here
docker compose stop worker         # now @mentions create notifications but emails queue up
docker compose start worker        # queued tasks drain
```
✅ **Checkpoint:** the web request never blocks on email — the worker does it, and the
app keeps working even while the worker is briefly down.

Tear down (keep data) or wipe it:
```bash
docker compose down                # stop, keep volumes
docker compose down -v             # also delete pgdata/miniodata
```

---

## What you learned
- One backend image serves three roles via the entrypoint argument.
- Multi-stage builds + non-root + standalone output make lean, safer images.
- 12-factor config means containerizing needed no code changes.
- Compose wires seven services into the full working app.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 13](../13-kubernetes-deploy/).
