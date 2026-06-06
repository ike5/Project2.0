# Challenge 15 — Reference Solution

### 1. PID isolation
```bash
sudo unshare --pid --fork --mount-proc bash
  echo "I am PID $$"     # 1
  ps -e                  # only the namespace's processes (bash, ps)
  exit
```
> **PID namespaces** give the process its own process-ID space; combined with
> `--mount-proc`, `/proc` reflects only the namespace, so the host's processes are
> invisible. This is one of the namespaces a container uses.

### 2. VM vs container
> **Fast start (container):** (1) no guest OS/kernel to boot — it's just processes on the
> running host kernel; (2) image layers are already on disk and shared (overlay fs), so
> there's nothing to "power on." **VM security advantage:** a full **hypervisor + separate
> kernel** boundary means a kernel-level exploit in the guest doesn't directly reach the
> host — stronger isolation than containers, which share the host kernel.

### 3. Persist data (bind mount)
```bash
mkdir -p ~/site && echo "<h1>v1</h1>" > ~/site/index.html
podman run -d --name web -p 8080:80 \
  -v ~/site:/usr/share/nginx/html:ro,Z \
  docker.io/library/nginx
curl -s localhost:8080            # <h1>v1</h1>
echo "<h1>v2</h1>" > ~/site/index.html
curl -s localhost:8080            # <h1>v2</h1>  — changed live, no rebuild
podman rm -f web
```
(`:Z` relabels for SELinux on RHEL; harmless elsewhere. Use `:ro` for read-only.)

### 4. Custom nginx image
`Containerfile`:
```dockerfile
FROM docker.io/library/nginx:alpine
COPY index.html /usr/share/nginx/html/index.html
```
```bash
echo "<h1>built image</h1>" > index.html
podman build -t mysite .
podman run -d --name mysite -p 8081:80 mysite
curl -s localhost:8081            # <h1>built image</h1>
podman rm -f mysite
```

### 5. Resource cap
```bash
podman run -d --name capped --memory 128m --cpus 0.25 docker.io/library/nginx
podman stats --no-stream capped          # MEM LIMIT 128MB; CPU throttled to 0.25
cat /sys/fs/cgroup/.../memory.max         # the enforced limit (path varies)
podman rm -f capped
```
> **cgroups** (control groups) enforce CPU/memory/IO limits; `--memory`/`--cpus` set the
> cgroup constraints the kernel applies.
