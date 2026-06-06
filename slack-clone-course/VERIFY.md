# VERIFY — End-to-End Smoke Test

Use this to confirm your environment and the app actually work. Early modules only
exercise the first few checks; by the capstone you should pass them all. Run it
whenever something feels broken to localize the problem.

---

## 0. Toolchain (after Module 00)

```bash
python --version     # 3.12.x
node --version       # v20.x or newer
docker version       # Client AND Server sections present
kind version
kubectl version --client
helm version
```
✅ All commands print a version with no errors.

## 1. Local data services

```bash
cd slack-clone-course/00-setup
docker compose -f compose.dev.yml up -d
docker compose -f compose.dev.yml ps     # postgres + redis = "running"/healthy
```
✅ Both containers are healthy. Postgres on `5432`, Redis on `6379`.

## 2. Backend boots (after Module 02+)

```bash
cd ../apps/slack-backend
python manage.py migrate            # all migrations apply, no errors
python manage.py runserver
curl -s localhost:8000/api/health/  # {"status":"ok"}
```
✅ Health endpoint returns `ok`; `/admin/` loads in a browser.

## 3. Auth round-trip (after Module 03)

```bash
# register, then log in to get tokens
curl -s -X POST localhost:8000/api/auth/register/ \
  -H 'content-type: application/json' \
  -d '{"email":"a@example.com","username":"ann","password":"slackpass123"}'

curl -s -X POST localhost:8000/api/auth/login/ \
  -H 'content-type: application/json' \
  -d '{"email":"a@example.com","password":"slackpass123"}'   # → access + refresh
```
✅ You receive `access` and `refresh` tokens; a protected endpoint accepts the
access token and rejects a missing/expired one.

## 4. Real-time messaging (after Module 05–06)

```bash
# in two terminals, connect to the same channel (use a real token + channel id)
npx wscat -c "ws://localhost:8000/ws/channels/1/?token=$ACCESS"
# send {"type":"message.new","text":"hi"} from one → it arrives in the other
```
✅ Messages broadcast to all connections in the channel; typing + presence update.

## 5. Async email & notifications (after Module 07)

```bash
celery -A config worker -l info        # worker starts, registers tasks
celery -A config beat -l info          # scheduler starts
# invite a user or @mention someone, then check MailHog at http://localhost:8025
```
✅ The worker logs the task; the email appears in MailHog.

## 6. Webhooks (after Module 08)

```bash
# post a signed payload to an incoming webhook
curl -s -X POST localhost:8000/api/webhooks/in/<token>/ \
  -H 'content-type: application/json' -d '{"text":"deploy finished ✅"}'
```
✅ The message appears in the target channel; outgoing webhooks fire with a valid
`X-Slackclone-Signature` HMAC header.

## 7. Frontend (after Module 09–11)

```bash
cd ../slack-frontend
npm install && npm run dev          # http://localhost:3000
```
✅ You can register/login, see channels, send and receive messages live, upload a
file, and search history.

## 8. Full stack via Docker Compose (after Module 12)

```bash
cd slack-clone-course
docker compose up --build
```
✅ Postgres, Redis, MailHog, MinIO, web, worker, beat, and frontend all come up;
the app works end-to-end at `http://localhost:3000`.

## 9. Kubernetes & high availability (after Module 13–15)

```bash
kubectl get pods -n slack            # all web/worker/beat/frontend Pods Ready
kubectl get cluster -n slack         # CloudNativePG cluster healthy (1 primary, 2 replicas)
```
✅ Every Pod is `Ready`; Ingress serves the app.

### Failure drills (the real HA proof — Module 15 & 17)

```bash
# Kill a web Pod — traffic keeps flowing, a replacement schedules
kubectl delete pod -n slack -l app=web --field-selector ... 

# Kill the Postgres primary — the operator promotes a replica
kubectl delete pod -n slack <primary-pod>
kubectl get cluster -n slack -w      # new primary elected, app reconnects
```
✅ The app stays available (or recovers within seconds) through both drills.
