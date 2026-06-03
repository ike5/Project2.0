# Troubleshooting: "My Pod Won't Start" Decision Tree

Kubernetes almost always tells you what's wrong — you just have to look in the
right place. **Start here, every time:**

```bash
kubectl get pods                 # what STATUS is it in?
kubectl describe pod <name>      # scroll to the Events section at the bottom
kubectl logs <name>              # what did the app itself say?
kubectl logs <name> --previous   # if it already crashed and restarted
```

90% of problems are solved by reading the **Events** in `describe` and the **logs**.

---

## Decode the STATUS column

### `Pending` — not scheduled / not started yet
The scheduler can't place it, or the image isn't down yet.
```bash
kubectl describe pod <name>   # look at Events
```
- **"Insufficient cpu/memory"** → no node has room. Lower `resources.requests`,
  scale down other workloads, or add a node.
- **"node(s) had untolerated taint"** → the Pod needs a toleration (Module 08).
- **"didn't match node selector / affinity"** → your `nodeSelector`/affinity rules
  match no node.
- **"pod has unbound immediate PersistentVolumeClaims"** → PVC isn't bound (Module 06).

### `ImagePullBackOff` / `ErrImagePull` — can't get the image
```bash
kubectl describe pod <name>   # Events show the exact pull error
```
- **Typo in image name or tag** → fix `image:`.
- **Image is local only** → with kind you must `kind load docker-image <img> --name k8s-course`.
- **Private registry, no creds** → create an `imagePullSecret`.
- **Tag doesn't exist** → check the tag actually exists in the registry.

### `CrashLoopBackOff` — starts, then crashes, repeatedly
The container *runs* but exits with an error; Kubernetes keeps restarting it with
growing back-off.
```bash
kubectl logs <name> --previous   # the crash is almost always explained here
```
- App throws on startup (bad config, missing env var, can't reach a dependency).
- `command`/`args` are wrong, or the entrypoint exits immediately.
- A **liveness probe** is failing and killing a healthy-but-slow app → fix the probe
  (raise `initialDelaySeconds`, use a `startupProbe`).

### `OOMKilled` (seen in `describe` → Last State)
The container exceeded its memory **limit** and was killed.
- Raise `resources.limits.memory`, or fix a memory leak / oversized workload.

### `CreateContainerConfigError`
A referenced ConfigMap/Secret or key doesn't exist.
```bash
kubectl describe pod <name>   # Events name the missing ConfigMap/Secret
```

### `Init:...` (stuck on an init container)
An init container hasn't completed.
```bash
kubectl logs <name> -c <init-container-name>
```

### `0/1 Running` but app unreachable
The Pod is Running but a **readiness probe** is failing, so it's not in the Service.
```bash
kubectl describe pod <name>   # Readiness probe failed: ...
```

---

## "My Service has no endpoints / I can't reach my app"

```bash
kubectl get endpoints <service>     # empty? then no Pods match the selector
kubectl get pods --show-labels      # do the pod labels match the Service selector?
```
- **Selector mismatch** — Service `spec.selector` must equal the Pods' labels.
- **Wrong `targetPort`** — Service `targetPort` must equal the container's port.
- **Pods not Ready** — failing readiness probes are excluded from endpoints.
- Test inside the cluster:
  ```bash
  kubectl run tmp --rm -it --image=busybox -- sh
  # then: wget -qO- http://<service-name>.<namespace>.svc.cluster.local
  ```

---

## "DNS isn't resolving"

```bash
kubectl get pods -n kube-system -l k8s-app=kube-dns   # is CoreDNS healthy?
kubectl run tmp --rm -it --image=busybox -- nslookup kubernetes.default
```

---

## General-purpose investigation toolkit

```bash
kubectl get events -A --sort-by=.lastTimestamp   # cluster-wide recent events
kubectl describe node <node>                     # node pressure / capacity issues
kubectl top pods / kubectl top nodes             # resource usage (needs metrics-server)
kubectl get pod <name> -o yaml                   # inspect full spec + status
kubectl exec -it <name> -- sh                    # poke around inside
kubectl debug -it <name> --image=busybox --target=<container>   # for distroless images
```

---

**Mental model:** `describe` tells you what Kubernetes is trying and failing to do
(scheduling, pulling, mounting, probing). `logs` tells you what your *application*
did. Almost every issue is one or the other.
