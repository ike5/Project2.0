# Module 15 — Containers & Virtualization (and more)

**Goal:** understand the kernel features behind containers and run them with Podman/
Docker — the "beyond LPI" piece that connects Linux to modern infrastructure (and your
Kubernetes course). ⏱️ ~1.5 h · 🎯 Prereq: 00–14.

---

## 1. VMs vs containers

- A **virtual machine** runs a full guest OS on virtualized hardware (via a hypervisor:
  KVM/QEMU, VirtualBox). Strong isolation; heavier (GBs, boots in seconds).
- A **container** is just **isolated processes on the host kernel** — its own view of the
  filesystem, network, and process tree, but **no separate kernel**. Lightweight (MBs,
  starts in milliseconds).

```
   VMs                              Containers
 ┌──────────────┐                ┌─────────────────────────────┐
 │ guest OS x N │                │ app │ app │ app  (processes)│
 │ hypervisor   │                ├─────┴─────┴─────────────────┤
 │ host kernel  │                │     shared host kernel       │
 └──────────────┘                └─────────────────────────────┘
```

## 2. The kernel features that make containers

Containers aren't a single feature — they're a combination:
- **Namespaces** — give a process its own *view* of a resource: `pid` (process tree),
  `net` (interfaces), `mnt` (filesystem), `uts` (hostname), `ipc`, `user` (UID mapping).
- **cgroups** (control groups) — *limit and account* resources: CPU, memory, I/O.
- **Union/overlay filesystems** — layer a read-only image with a writable top layer.
- **Capabilities / seccomp / SELinux/AppArmor** — drop privileges and restrict syscalls.

See them on a running container:
```bash
lsns                    # list namespaces (if util-linux is recent)
cat /proc/self/cgroup   # this process's cgroup
systemd-cgls | head     # the cgroup tree
```

## 3. Run containers with Podman (daemonless) or Docker

Podman is the RHEL default and runs **rootless**; Docker is ubiquitous. The CLIs are
nearly identical (`alias docker=podman` often works).
```bash
sudo apt install -y podman          # or docker.io
podman run --rm hello-world
podman run -d --name web -p 8080:80 docker.io/library/nginx
podman ps                            # running containers
curl -s localhost:8080 | head -3     # reach nginx in the container
podman exec -it web sh               # shell inside
podman logs web
podman stop web && podman rm web
podman images                        # local images
```
(Replace `podman` with `docker` if you installed Docker — same commands.)

## 4. Images & a Containerfile/Dockerfile

An **image** is a packaged filesystem + metadata, built in **layers** from a recipe:
```dockerfile
FROM docker.io/library/python:3.12-slim
WORKDIR /app
COPY app.py .
CMD ["python", "app.py"]
```
```bash
podman build -t myapp .
podman run --rm myapp
```

## 5. Where this goes next

Containers are the unit Kubernetes orchestrates. The Linux skills you built here —
processes, namespaces/cgroups, networking, storage, users/permissions — are exactly what
make containers (and Kubernetes) comprehensible rather than magic. (See the separate
**Kubernetes course**.)

> Other virtualization worth knowing: **KVM/QEMU** (`virsh`, `virt-install`) for full VMs,
> and **systemd-nspawn**/LXC for lightweight system containers.

---

## Do the lab
Inspect namespaces/cgroups, run and build a container, and reach a service inside it.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
VM vs container · hypervisor · namespace (pid/net/mnt/uts/user) · cgroup · overlay fs ·
capabilities/seccomp · Podman/Docker (`run`/`ps`/`exec`/`logs`/`build`) · image/layer ·
Containerfile/Dockerfile · rootless

**Next →** [Module 16: Capstone — Build & Harden a Server](../16-capstone/)
