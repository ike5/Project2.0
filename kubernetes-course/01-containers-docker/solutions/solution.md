# Challenge 01 — Reference Solution

### 1. Build a v2
Edit `apps/web-api/app.py`:
```python
GREETING = os.environ.get("GREETING", "Ahoy from MY web-api!")
```
```bash
cd apps/web-api
docker build -t web-api:2.0 .
docker run --rm -d --name v2 -p 8080:8080 web-api:2.0
curl -s localhost:8080/ ; echo      # shows "Ahoy from MY web-api!"
docker rm -f v2
```

### 2. Override config at run time (no rebuild)
```bash
docker run --rm -d --name v1 -p 8080:8080 \
  -e COLOR=purple -e APP_VERSION=9.9.9 web-api:1.0
curl -s localhost:8080/config ; echo   # color=purple, version=9.9.9
docker rm -f v1
```

### 3. Inspect a running container
```bash
docker run -d --name x -p 8080:8080 web-api:1.0
docker exec x whoami            # appuser
docker exec x printenv PORT     # 8080
docker logs x                   # Flask startup logs
docker rm -f x
```

### 4. Load v2 into kind and run as `web2`
```bash
kind load docker-image web-api:2.0 --name k8s-course
kubectl run web2 --image=web-api:2.0 --port=8080 \
  --overrides='{"spec":{"containers":[{"name":"web2","image":"web-api:2.0","imagePullPolicy":"Never"}]}}'
kubectl wait --for=condition=Ready pod/web2 --timeout=60s
kubectl port-forward pod/web2 8080:8080 &
curl -s localhost:8080/ ; echo   # your custom greeting
kill %1
kubectl delete pod web2
```

### 5. The gotcha, explained
> kind clusters run in their own Docker containers and can't see your laptop's
> local Docker images; without `imagePullPolicy: Never` the kubelet tries to
> **pull `web-api:2.0` from a registry**, where it doesn't exist, giving
> `ImagePullBackOff`. (You also must `kind load` the image first.)
