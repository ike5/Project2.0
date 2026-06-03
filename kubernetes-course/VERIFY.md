# End-to-End Verification

Use this **once after Module 00** to confirm your whole toolchain works, and any
time something feels broken. If every step here passes, you're ready for the course.

## 0. Tools are installed

```bash
docker version          # client + server both respond (Docker Desktop running)
kind version            # e.g. kind v0.23.x
kubectl version --client
helm version
```
✅ Expected: each command prints a version. If `docker version` errors on the
*server*, start **Docker Desktop** and wait for the whale icon to settle.

## 1. Cluster is up with 3 nodes

```bash
cd 00-setup
./scripts/create-cluster.sh      # idempotent: skips if it already exists
kubectl get nodes
```
✅ Expected: **3 nodes**, all `Ready`:
```
NAME                       STATUS   ROLES           AGE   VERSION
k8s-course-control-plane   Ready    control-plane   1m    v1.30.x
k8s-course-worker          Ready    <none>          1m    v1.30.x
k8s-course-worker2         Ready    <none>          1m    v1.30.x
```

## 2. The api-server answers

```bash
kubectl get ns
kubectl cluster-info
```
✅ Expected: namespaces listed (`default`, `kube-system`, …) and a control-plane URL.

## 3. Build → load → run the sample app (the core loop)

```bash
cd ../apps/web-api
docker build -t web-api:1.0 .
kind load docker-image web-api:1.0 --name k8s-course

kubectl run smoke --image=web-api:1.0 --port=8080 \
  --overrides='{"spec":{"containers":[{"name":"smoke","image":"web-api:1.0","imagePullPolicy":"Never"}]}}'
kubectl wait --for=condition=Ready pod/smoke --timeout=60s
```
✅ Expected: `pod/smoke condition met`.

> `imagePullPolicy: Never` tells Kubernetes "don't try to pull from a registry —
> the image is already loaded locally." Forgetting this with a local image is the
> #1 cause of `ImagePullBackOff` on kind.

## 4. Reach the app

```bash
kubectl port-forward pod/smoke 8080:8080 &
sleep 2
curl -s localhost:8080/ ; echo
curl -s localhost:8080/healthz ; echo
kill %1            # stop the port-forward
```
✅ Expected:
```
{"color":"blue","message":"Hello from web-api","served_by":"smoke","version":"1.0.0"}
{"status":"ok"}
```

## 5. Clean up the smoke test

```bash
kubectl delete pod smoke
```

---

🎉 **All green?** Your environment is solid. Head to
[Module 01: Containers & Docker Primer](./01-containers-docker/).

If something failed, see [cheatsheets/troubleshooting.md](./cheatsheets/troubleshooting.md)
and the Troubleshooting section in [00-setup/README.md](./00-setup/README.md).
