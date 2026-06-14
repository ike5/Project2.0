# Lab 13 — Deploy to Kubernetes

**You'll:** build and load the images, install the ingress, apply the base manifests,
run migrations as a Job, and use the app at `http://slack.local`.

⏱️ ~60 min. The kind cluster from Module 00 (`create-cluster.sh`). Run from
`slack-clone-course`.

---

## Part A — Build and load images into kind

```bash
docker build -t slack-backend:dev ./apps/slack-backend
docker build -t slack-frontend:dev \
  --build-arg NEXT_PUBLIC_API_URL=http://slack.local \
  --build-arg NEXT_PUBLIC_WS_URL=ws://slack.local \
  ./apps/slack-frontend

kind load docker-image slack-backend:dev slack-frontend:dev --name slack
```
✅ **Checkpoint:** both images are loaded (the `kind load` output confirms each).

---

## Part B — Install the nginx ingress

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
kubectl wait -n ingress-nginx --for=condition=Available deploy/ingress-nginx-controller --timeout=120s
```

Map the hostname locally:
```bash
echo "127.0.0.1 slack.local" | sudo tee -a /etc/hosts
```

---

## Part C — Apply the app

```bash
kubectl apply -k k8s/base
kubectl get pods -n slack -w        # wait until web/worker/beat/frontend are Running
```
✅ Expected: `postgres`, `redis`, `mailhog`, `minio`, `web` (×2), `worker` (×2),
`beat` (×1), `frontend` (×2) all `Running`/`Ready`.

> Hit `ImagePullBackOff`? You forgot `kind load` or the `imagePullPolicy` — the Docker
> primer's #1 gotcha.

---

## Part D — Run migrations

```bash
kubectl apply -f k8s/base/migrate-job.yaml
kubectl wait -n slack --for=condition=complete job/migrate --timeout=120s
kubectl logs -n slack job/migrate | tail
```
✅ Expected: migrations apply and the Job completes. Create an admin:
```bash
kubectl exec -n slack deploy/web -- python manage.py createsuperuser --noinput \
  --email admin@example.com --username admin || true
kubectl exec -n slack -it deploy/web -- python manage.py changepassword admin
```

---

## Part E — Use it

Open <http://slack.local> — register, create a workspace via
<http://slack.local/admin/>, and chat. WebSockets flow through the ingress
(`/ws`), email goes to MailHog, uploads to MinIO — all in the cluster.

✅ **Checkpoint:** the same app you ran in compose now runs across the cluster's nodes.
Confirm pods are spread:
```bash
kubectl get pods -n slack -o wide | awk '{print $1, $7}'
```

---

## Part F — Self-healing preview

```bash
kubectl delete pod -n slack -l app=web --grace-period=0 --force | head -1
kubectl get pods -n slack -w        # a replacement schedules immediately
```
✅ The Deployment recreates the pod; because there were 2 replicas, the app stayed up
the whole time. (Full HA proof is Module 15/17.)

---

## What you learned
- The app maps to Deployments + Services + an Ingress, with config/secrets as env.
- One image runs web/worker/beat; beat must stay a singleton.
- Migrations run once as a Job before web rolls out.
- kind needs `kind load` + `imagePullPolicy: IfNotPresent` for local images.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 14](../14-stateful-operators/).
