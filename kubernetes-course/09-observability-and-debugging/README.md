# Module 09 — Observability & Debugging

**Goal:** become the person who can figure out *why* something is broken — and stand
up a real metrics stack (Prometheus + Grafana) to see your cluster.

⏱️ ~2.5 hours · 🎯 Prereq: Modules 00–08 (metrics-server installed in 08).

---

## Part 1 — The debugging toolkit

Almost every problem is solved with four commands. Internalize this order:

```bash
kubectl get pods               # 1. What STATUS? (Pending/CrashLoopBackOff/...)
kubectl describe pod <name>    # 2. Read the EVENTS at the bottom (scheduling, pulls, probes)
kubectl logs <name>            # 3. What did the APP say?
kubectl logs <name> --previous # 4. ...in the instance that crashed
```

> `describe` tells you what *Kubernetes* tried and failed to do.
> `logs` tells you what your *application* did. Almost everything is one or the other.

See the full **[troubleshooting decision tree](../cheatsheets/troubleshooting.md)**.

### Beyond the basics
```bash
kubectl get events --sort-by=.lastTimestamp     # timeline of what just happened
kubectl exec -it <pod> -- sh                     # poke around inside
kubectl debug -it <pod> --image=busybox --target=<container>   # ephemeral debug container
kubectl port-forward <pod> 8080:8080             # reach it locally
kubectl top pods / kubectl top nodes             # resource usage (needs metrics-server)
```

`kubectl debug` is gold for **distroless** images that have no shell: it attaches a
*temporary* debug container (with your tools) that shares the target's process and
network namespaces.

## Part 2 — The failure mode flashcards

| Symptom | Likely cause | First move |
|---------|-------------|-----------|
| `Pending` | no node fits (resources/taints/affinity/unbound PVC) | `describe` → Events |
| `ImagePullBackOff` | bad image name/tag, or local image not loaded into kind | `describe` → pull error |
| `CrashLoopBackOff` | app exits on start, or aggressive liveness probe | `logs --previous` |
| `OOMKilled` | memory limit too low / leak | `describe` → Last State |
| `CreateContainerConfigError` | missing ConfigMap/Secret/key | `describe` → Events |
| Running but 0/1 Ready | readiness probe failing | `describe` → Readiness |
| Service unreachable | selector/targetPort mismatch, not Ready | `get endpoints` |

## Part 3 — The three pillars of observability

- **Logs** — discrete events (`kubectl logs`; in prod, shipped by a DaemonSet like
  Fluent Bit to a store like Loki/Elasticsearch).
- **Metrics** — numeric time series (CPU, request rate, latency). Collected by
  **Prometheus**, visualized in **Grafana**.
- **Traces** — the path of a request across services (OpenTelemetry/Jaeger). Beyond
  our scope, but know the word.

## Part 4 — A real metrics stack: kube-prometheus-stack

We install the community **kube-prometheus-stack** Helm chart, which bundles
Prometheus (scrapes & stores metrics), Grafana (dashboards), Alertmanager, and a set
of preconfigured cluster dashboards. This is the de-facto standard monitoring stack.

```bash
helm repo add prometheus-community https://prometheus-community.github.io/helm-charts
helm install monitoring prometheus-community/kube-prometheus-stack -n monitoring --create-namespace
```

You'll port-forward Grafana and explore prebuilt dashboards of *your* cluster.

---

## Do the lab
Diagnose four deliberately-broken Pods using only `kubectl`, use `kubectl debug`,
then install Prometheus + Grafana and explore dashboards. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Manifests (all broken on purpose — your job is to diagnose)
- [`broken-image.yaml`](./manifests/broken-image.yaml) — ImagePullBackOff
- [`broken-crash.yaml`](./manifests/broken-crash.yaml) — CrashLoopBackOff
- [`broken-config.yaml`](./manifests/broken-config.yaml) — missing ConfigMap
- [`broken-pending.yaml`](./manifests/broken-pending.yaml) — unschedulable

## Key terms
describe · events · logs (`--previous`) · `kubectl debug` · ephemeral container ·
logs/metrics/traces · Prometheus · Grafana · kube-prometheus-stack

**Next →** [Module 10: Packaging — Helm & Kustomize](../10-packaging-helm-kustomize/)
