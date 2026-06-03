# Lab 01 — Build, Run, and Load a Container Image

**You'll:** build the `web-api` image, run it with Docker, inspect it, then load it
into your kind cluster (the step that connects Docker to Kubernetes).

⏱️ ~40 min. All commands assume you're in the course root unless noted.

---

## Part A — Run someone else's image

The fastest way to feel containers: run a public image.

```bash
docker run --rm -p 8080:80 nginx:1.27
```
- `--rm` deletes the container when it stops.
- `-p 8080:80` maps your Mac's port 8080 → the container's port 80.

Open <http://localhost:8080> — you'll see the nginx welcome page. Back in the
terminal, press `Ctrl+C` to stop it.

```bash
docker images          # nginx:1.27 is now cached locally
docker ps -a           # the stopped container (none if you used --rm)
```

✅ **Checkpoint:** you served a web app without installing nginx on your Mac.

---

## Part B — Build your own image

```bash
cd apps/web-api
cat Dockerfile        # read it — every line is commented
docker build -t web-api:1.0 .
```
Watch the build run each Dockerfile instruction as a **step/layer**.

✅ Expected (last lines):
```
 => naming to docker.io/library/web-api:1.0
```

Verify it exists:
```bash
docker images web-api
# REPOSITORY   TAG   IMAGE ID       SIZE
# web-api      1.0   xxxxxxxxxxxx   ~150MB
```

### See layer caching in action
Re-run the build — it's near-instant because nothing changed:
```bash
docker build -t web-api:1.0 .      # => CACHED on every step
```
Now touch the code and rebuild — only the code layer rebuilds, not `pip install`:
```bash
touch app.py
docker build -t web-api:1.0 .      # pip layer is CACHED; COPY app.py reruns
```

✅ **Checkpoint:** you understand why `COPY requirements.txt` comes before `COPY app.py`.

---

## Part C — Run and inspect your container

```bash
docker run -d --name myapi -p 8080:8080 web-api:1.0   # -d = detached (background)
docker ps                                              # see it running
curl -s localhost:8080/ ; echo
curl -s localhost:8080/config ; echo
```
✅ Expected:
```
{"color":"blue","message":"Hello from web-api","served_by":"<container-id>","version":"1.0.0"}
```

Look inside the running container:
```bash
docker logs myapi                 # the app's stdout
docker exec -it myapi sh          # get a shell inside
  # inside the container:
  ls ; whoami ; env | grep PORT ; exit
```
Note `whoami` prints `appuser`, not `root` — because the Dockerfile set `USER appuser`.

### Pass config via environment variables
Containers are configured with env vars (this is exactly how Kubernetes injects
ConfigMaps/Secrets later):
```bash
docker rm -f myapi
docker run -d --name myapi -p 8080:8080 -e COLOR=green -e APP_VERSION=2.0.0 web-api:1.0
curl -s localhost:8080/ ; echo      # color is now green, version 2.0.0
```

Clean up:
```bash
docker rm -f myapi
```

---

## Part D — The bridge to Kubernetes: load into kind

Your kind cluster runs in separate Docker containers and **cannot see images in
your local Docker** by default. You must explicitly load them:

```bash
# make sure the cluster is up (Module 00)
kubectl get nodes

# load your locally-built image into the kind cluster
kind load docker-image web-api:1.0 --name k8s-course
```
✅ Expected: `Image: "web-api:1.0" with ID ... not yet present on node ..., loading...`

Now run it as a Pod (a preview of Module 03):
```bash
kubectl run web --image=web-api:1.0 --port=8080 \
  --overrides='{"spec":{"containers":[{"name":"web","image":"web-api:1.0","imagePullPolicy":"Never"}]}}'
kubectl get pods -w        # wait until Running, then Ctrl+C
```
> `imagePullPolicy: Never` = "use the loaded local image; don't pull from a
> registry." **Forgetting this is the #1 beginner gotcha** — you'd get `ImagePullBackOff`.

Reach it:
```bash
kubectl port-forward pod/web 8080:8080 &
curl -s localhost:8080/ ; echo
kill %1
```

Clean up:
```bash
kubectl delete pod web
```

---

## What you learned
- Images are templates; containers are running instances.
- Dockerfiles build images in cached layers (order matters).
- Containers are configured via environment variables.
- **kind needs `kind load docker-image` + `imagePullPolicy: Never` for local images.**

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 02](../02-k8s-fundamentals/).
