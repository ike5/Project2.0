# Challenge 13 — Reference Solution

### 1. Rolling update + rollback
```bash
docker build -t slack-backend:v2 ./apps/slack-backend
kind load docker-image slack-backend:v2 --name slack
kubectl set image -n slack deploy/web web=slack-backend:v2
kubectl rollout status -n slack deploy/web      # waits for healthy rollout
kubectl rollout undo  -n slack deploy/web       # back to the previous ReplicaSet
```
`maxUnavailable: 0` keeps full capacity during the roll; readiness probes gate traffic.

### 2. Scale by hand
```bash
kubectl scale -n slack deploy/web --replicas=4
kubectl get pods -n slack -l app=web
for i in $(seq 1 8); do curl -s slack.local/api/health/; echo; done
```
The `web` Service round-robins across the 4 ready endpoints.

### 3. ConfigMap change
```bash
kubectl edit configmap/backend-config -n slack     # change FRONTEND_ORIGIN
kubectl rollout restart deploy/web -n slack
```
> `envFrom` reads the ConfigMap **at pod start**, so changing it doesn't touch running
> pods. `rollout restart` recreates the pods, which re-read the new values. (Mounted
> ConfigMap *files* update live, but env vars do not.)

### 4. ImagePullBackOff
```bash
kubectl set image -n slack deploy/web web=slack-backend:nope
kubectl get pods -n slack          # ImagePullBackOff
kubectl set image -n slack deploy/web web=slack-backend:dev   # fix
```
> kind nodes can't see your laptop's Docker images; with `imagePullPolicy: IfNotPresent`
> the kubelet uses an image already present on the node — which is why you must
> `kind load` it first. A tag that was never loaded (or never pushed to a registry)
> can't be pulled → `ImagePullBackOff`.

### 5. Why beat is a singleton
> Celery Beat is a **scheduler**: it enqueues each periodic task when its time comes.
> Two Beat processes both reach 08:00 and both enqueue `send_daily_digest`, so every
> user gets the digest **twice** (and every periodic task double-fires). `web` and
> `worker` are stateless request/task processors — running many is the whole point and
> causes no duplication. Hence beat is `replicas: 1` with a `Recreate` strategy so a
> rollout never briefly runs two.
