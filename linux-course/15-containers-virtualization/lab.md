# Lab 15 — Containers Hands-On

**You'll:** see the kernel features behind containers, then run and build one. ⏱️ ~45 min.
In your VM.

---

## Part A — Namespaces & cgroups (the foundation)
```bash
# Your shell already lives in namespaces:
ls -l /proc/self/ns/                 # pid, net, mnt, uts, user, ...
cat /proc/self/cgroup                # which cgroup this process is in
# Create a new UTS+PID namespace and see isolation (needs unshare):
sudo unshare --pid --fork --mount-proc bash -c 'echo "PID inside: $$"; ps -e | head'
#   inside, this bash is PID 1 and ps shows only the namespace's processes
```
✅ `$$` is a low number and `ps` shows a tiny process list — you're in a separate PID
namespace. That isolation is the essence of a container.

## Part B — Install a container engine
```bash
sudo apt install -y podman
podman --version
```
(If you prefer Docker: `sudo apt install -y docker.io` and use `docker` below.)

## Part C — Run a container
```bash
podman run --rm docker.io/library/hello-world
podman run -d --name web -p 8080:80 docker.io/library/nginx
podman ps
curl -s localhost:8080 | head -3       # nginx, running in a container, reachable on 8080
```
✅ A web server is running in an isolated container, port-mapped to the host.

## Part D — Look inside
```bash
podman exec -it web sh
  # inside the container:
  hostname            # a container ID, not your VM's hostname (uts namespace)
  ps aux              # only nginx processes (pid namespace)
  ls /                # the image's filesystem (mnt namespace)
  exit
podman logs web | tail
```
✅ Inside, the process tree, hostname, and filesystem are the container's own — namespaces
at work.

## Part E — Limit resources (cgroups)
```bash
podman run -d --name limited --memory 64m --cpus 0.5 docker.io/library/nginx
podman stats --no-stream limited       # MEM LIMIT shows 64M
podman rm -f limited
```

## Part F — Build your own image
```bash
mkdir -p ~/ctr && cd ~/ctr
cat > app.py <<'EOF'
print("hello from a container I built")
EOF
cat > Containerfile <<'EOF'
FROM docker.io/library/python:3.12-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
EOF
podman build -t myapp .
podman run --rm myapp                   # prints the message
podman images | grep myapp              # your image, built in layers
```

## Cleanup
```bash
podman rm -f web 2>/dev/null
podman rmi myapp docker.io/library/nginx docker.io/library/python:3.12-slim 2>/dev/null
rm -rf ~/ctr
```

## What you learned
- Namespaces (pid/uts/mnt/net) and cgroups are the kernel features behind containers.
- Run/inspect/limit containers with Podman (or Docker) — same skills.
- Build an image from a Containerfile/Dockerfile in layers.
- Why your Linux fundamentals make containers (and Kubernetes) make sense.

➡️ **[challenge.md](./challenge.md)** then the [Capstone](../16-capstone/).
