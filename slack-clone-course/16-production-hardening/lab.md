# Lab 16 — Make It Observable and Secure

**You'll:** enable JSON logging and Sentry, install Prometheus + Grafana, turn on TLS,
and enforce NetworkPolicies — then prove a blocked flow.

⏱️ ~60 min. The HA deployment from Module 15. Run from `slack-clone-course`.

---

## Part A — Structured logging

Add a JSON formatter to `LOGGING` in `config/settings.py` and a request-id middleware,
then redeploy web:
```python
LOGGING = {
  "version": 1,
  "disable_existing_loggers": False,
  "formatters": {"json": {"()": "pythonjsonlogger.jsonlogger.JsonFormatter",
                          "format": "%(asctime)s %(levelname)s %(name)s %(message)s"}},
  "handlers": {"console": {"class": "logging.StreamHandler", "formatter": "json"}},
  "root": {"handlers": ["console"], "level": "INFO"},
}
```
```bash
kubectl logs -n slack deploy/web | tail -3      # lines are now JSON objects
```
✅ **Checkpoint:** logs are machine-parseable.

---

## Part B — Sentry

```python
# config/settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration
from sentry_sdk.integrations.celery import CeleryIntegration
if env("SENTRY_DSN", default=""):
    sentry_sdk.init(dsn=env("SENTRY_DSN"), integrations=[DjangoIntegration(), CeleryIntegration()],
                    traces_sample_rate=0.1)
```
Trigger a deliberate error and confirm it appears in your Sentry project (or the logs
if you skip the DSN).

---

## Part C — Prometheus + Grafana

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install kps prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
kubectl -n monitoring port-forward svc/kps-grafana 3001:80
```
Add `django-prometheus` to the app, expose `/metrics`, and add a `ServiceMonitor` so
Prometheus scrapes web. In Grafana (<http://localhost:3001>), build a panel for request
rate, p95 latency, and error rate.
✅ **Checkpoint:** you can watch the golden signals while you use the app.

---

## Part D — TLS

```bash
kubectl apply -f https://github.com/cert-manager/cert-manager/releases/latest/download/cert-manager.yaml
kubectl -n cert-manager rollout status deploy/cert-manager
kubectl apply -f k8s/hardening/tls.yaml
kubectl get certificate -n slack          # slack-tls-cert becomes Ready
```
✅ Open <https://slack.local> (accept the self-signed cert). Sockets now use `wss://`.

---

## Part E — NetworkPolicies (and prove one)

> kind's default CNI doesn't enforce NetworkPolicies. Install Calico first if you want
> real enforcement; otherwise read and reason about them.

```bash
kubectl apply -f k8s/hardening/networkpolicy.yaml
```
Prove Postgres rejects a non-backend pod:
```bash
kubectl run -n slack probe --image=postgres:16 --restart=Never -it --rm -- \
  psql "postgres://slack:slackpass@slack-pg-rw:5432/slack" -c '\l'
```
✅ Expected (with Calico): the connection **times out** — `probe` isn't labeled
`app in (web,worker,beat)`, so the policy blocks it. The real web pods still connect fine.

---

## What you learned
- JSON logs + Sentry turn failures into searchable, alertable events.
- Prometheus + Grafana surface the golden signals.
- cert-manager gives you HTTPS/`wss://` with auto-renewing certs.
- Default-deny NetworkPolicies shrink the blast radius of a compromised pod.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 17](../17-capstone/).
