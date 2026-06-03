# Module 04 — Configuration & Pod Lifecycle

**Goal:** stop hard-coding config into images. Inject configuration with ConfigMaps
and Secrets, set resource requests/limits, and keep apps healthy with probes.

⏱️ ~2 hours · 🎯 Prereq: Modules 00–03.

---

## 1. Why externalize config?

The same image should run in dev, staging, and prod with *different* settings.
Baking config into the image means rebuilding for every change and leaking secrets
into image layers. Instead, inject config at runtime via **ConfigMaps** and **Secrets**.

## 2. ConfigMaps

A **ConfigMap** stores non-secret config as key/value pairs (or whole files). Two
ways to consume it in a Pod:

```yaml
# (a) as environment variables
envFrom:
  - configMapRef:
      name: web-config
# or pick individual keys:
env:
  - name: COLOR
    valueFrom:
      configMapKeyRef: { name: web-config, key: COLOR }

# (b) as mounted files (each key becomes a file)
volumes:
  - name: cfg
    configMap: { name: web-config }
volumeMounts:
  - name: cfg
    mountPath: /etc/web
```

- **Env vars**: simplest, great for scalars. **Caveat:** env vars are read at
  container start — changing the ConfigMap does *not* update a running Pod's env;
  you must restart it (`kubectl rollout restart`).
- **Mounted files**: updates propagate to the file (eventually), good for config
  files and large blobs.

## 3. Secrets

A **Secret** is like a ConfigMap but intended for sensitive data (passwords, tokens,
keys). **Critical truth for beginners:**

> Kubernetes Secrets are **base64-encoded, NOT encrypted** by default. Anyone who
> can read the Secret object can trivially decode it.

Treat them as "slightly more careful config", not as a vault. Real protection
comes from: RBAC (Module 11), enabling **encryption at rest** for etcd, and/or
external secret managers (Vault, cloud KMS, External Secrets Operator).

Consume Secrets exactly like ConfigMaps (`secretKeyRef`, `envFrom.secretRef`, or
volume mounts). Prefer file mounts for real secrets (they don't show up in
`kubectl describe pod` env dumps or process listings as readily).

## 4. Resource requests & limits

```yaml
resources:
  requests: { cpu: "100m", memory: "128Mi" }   # guaranteed; used for SCHEDULING
  limits:   { cpu: "500m", memory: "256Mi" }   # ceiling; enforced at RUNTIME
```

- **requests** = what the Pod is guaranteed; the scheduler uses this to find a node
  with enough free capacity.
- **limits** = the maximum. Exceed the **memory** limit → the container is
  **OOMKilled**. Exceed the **CPU** limit → it's **throttled** (not killed).
- No requests/limits = "BestEffort" Pods, first to be evicted under pressure.

Setting sensible requests/limits is one of the highest-impact things you can do
for cluster stability. `m` = millicores (`1000m` = 1 CPU). `Mi`/`Gi` = binary units.

## 5. Health probes

Kubernetes checks container health with three probe types:

| Probe | Question | On failure |
|-------|----------|-----------|
| **liveness** | Is it alive? | restart the container |
| **readiness** | Can it serve traffic *now*? | remove from Service endpoints (no restart) |
| **startup** | Has it finished booting? | hold off liveness/readiness until it passes |

Probe handlers: `httpGet`, `tcpSocket`, or `exec` (run a command).

```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 8080 }
  initialDelaySeconds: 3
  periodSeconds: 10
readinessProbe:
  httpGet: { path: /readyz, port: 8080 }
  periodSeconds: 5
```

**Common mistake:** a too-aggressive liveness probe restarts a slow-but-healthy
app forever (`CrashLoopBackOff`). Fix with a **startupProbe** or larger
`initialDelaySeconds`. Our `web-api` exposes `/healthz`, `/readyz`, and a
`/toggle-ready` endpoint precisely so you can watch readiness in action.

## 6. restartPolicy

Pods have a `restartPolicy`: `Always` (default, for long-running apps),
`OnFailure`, or `Never` (the latter two used by Jobs — Module 07).

---

## Do the lab
Externalize `web-api`'s config to a ConfigMap + Secret, add resource limits and
probes, then watch a failing readiness probe pull a Pod out of rotation and an
OOM limit kill a greedy container. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests
- [`configmap.yaml`](./manifests/configmap.yaml) · [`secret.yaml`](./manifests/secret.yaml)
- [`web-deploy.yaml`](./manifests/web-deploy.yaml) — Deployment using them + probes + resources
- [`oom-demo.yaml`](./manifests/oom-demo.yaml) — a Pod that exceeds its memory limit

## Key terms
ConfigMap · Secret · base64 · requests · limits · OOMKilled · liveness · readiness ·
startup probe · restartPolicy

**Next →** [Module 05: Networking — Services & Ingress](../05-networking-services-ingress/)
