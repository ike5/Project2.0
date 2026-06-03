# Anatomy of a Kubernetes Manifest

Once you can read these four top-level keys, you can read *any* Kubernetes YAML.
Every object — Pod, Deployment, Service, Secret — has the same skeleton.

```yaml
apiVersion: apps/v1        # 1. Which API group + version defines this object
kind: Deployment           # 2. What kind of object this is
metadata:                  # 3. Who it is: name, namespace, labels, annotations
  name: web
  namespace: default
  labels:
    app: web
spec:                      # 4. What you WANT (the desired state)
  replicas: 3
  selector:
    matchLabels:
      app: web
  template:                #    a Pod template — the blueprint for the Pods to create
    metadata:
      labels:
        app: web           #    ⚠️ MUST match spec.selector.matchLabels above
    spec:
      containers:
        - name: web
          image: nginx:1.27
          ports:
            - containerPort: 80
```

## The four keys, explained

| Key | Question it answers | Notes |
|-----|---------------------|-------|
| `apiVersion` | *Which API contract?* | `v1` for core objects (Pod, Service, ConfigMap); `apps/v1` for Deployment/StatefulSet/DaemonSet; `batch/v1` for Job/CronJob; `networking.k8s.io/v1` for Ingress/NetworkPolicy. Use `kubectl explain <kind>` or `kubectl api-resources` to find the right one. |
| `kind` | *What object?* | Capitalized, singular: `Pod`, `Deployment`, `Service`. |
| `metadata` | *Who is it?* | At minimum `name`. Add `labels` (for selection), `namespace`, `annotations`. |
| `spec` | *What do I want?* | The interesting part. Shape varies by `kind`. **You write `spec`; Kubernetes fills in `status`.** |

## `spec` vs `status` (declarative model)

- **You** write `spec` = desired state.
- **Kubernetes** writes `status` = observed/actual state.
- The control loop continuously works to make `status` match `spec`.

When you `kubectl get pod x -o yaml`, you'll see a big `status:` block — you never
write that; the system does.

## The label/selector handshake (trips up everyone)

A Deployment finds *its* Pods by label. Three places must agree:

```yaml
spec:
  selector:
    matchLabels:
      app: web        # (A) what the Deployment looks for
  template:
    metadata:
      labels:
        app: web      # (B) the label stamped on created Pods — must match (A)
```

And a Service finds those same Pods the same way:

```yaml
# Service
spec:
  selector:
    app: web          # (C) must match the Pods' labels (B)
```

If `(A)` ≠ `(B)`, the Deployment errors. If `(C)` ≠ `(B)`, your Service has **no
endpoints** and traffic goes nowhere (a super common "why can't I reach my app?").

## Multiple objects in one file

Separate them with `---`:

```yaml
apiVersion: v1
kind: Service
metadata:
  name: web
spec:
  selector:
    app: web
  ports:
    - port: 80
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: web
# ...
```

## Common `spec.containers` fields

```yaml
containers:
  - name: web                 # required, unique within the pod
    image: myrepo/web:1.0     # required
    command: ["python"]       # overrides the image's ENTRYPOINT (optional)
    args: ["app.py"]          # overrides the image's CMD (optional)
    ports:
      - containerPort: 8080   # documentation/clarity; doesn't "open" anything by itself
    env:
      - name: LOG_LEVEL
        value: "debug"
    envFrom:
      - configMapRef:
          name: web-config
    resources:
      requests: { cpu: "100m", memory: "128Mi" }
      limits:   { cpu: "500m", memory: "256Mi" }
    volumeMounts:
      - name: data
        mountPath: /data
```

> `100m` = 100 millicores = 0.1 CPU. `128Mi` = 128 mebibytes. `Mi`/`Gi` are
> binary units; `M`/`G` are decimal — prefer `Mi`/`Gi`.

## Tips for writing YAML without pain

- **YAML is whitespace-sensitive.** Use 2 spaces, never tabs.
- **Generate, don't type:** `kubectl create deployment ... --dry-run=client -o yaml`.
- **Validate before applying:** `kubectl apply -f file.yaml --dry-run=server`.
- **Look up any field:** `kubectl explain deployment.spec.strategy`.
