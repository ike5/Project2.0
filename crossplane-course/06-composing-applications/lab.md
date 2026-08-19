# Lab 06 — One Resource, a Whole Stack

**You'll:** ship a database, a bucket, a Deployment, a Service, and an Ingress from
one 8-line XR — then prove the database password was never visible to a human.
⏱️ ~80 min.

> Prereqs: Modules 04–05. Providers, functions, MRAP, Secret, and ProviderConfig
> installed.

---

## Part A — Add RDS and build the sample app

```bash
cd 06-composing-applications
kubectl apply -f manifests/providers.yaml
kubectl wait provider/provider-aws-rds --for=condition=Healthy --timeout=10m
kubectl apply -f manifests/functions.yaml
kubectl get providers,functions
```
✅ Expected: all `HEALTHY=True`. Note `providers.yaml` also widens the MRAP to
activate the RDS types — without that, `kind: Instance` won't resolve.

Build the sample app and load it into the cluster:
```bash
cd manifests/app
docker build -t xp-course/sample-app:1.0 .
kind load docker-image xp-course/sample-app:1.0 --name xp-course
cd ../..
```
✅ Expected: `Image: "xp-course/sample-app:1.0" with ID ... not yet present on node
"xp-course-worker", loading...`

> `kind load` is not optional. The image exists only on your machine; the cluster
> has no registry to pull it from.

## Part B — Install the API

```bash
kubectl create ns team-payments
kubectl apply -f manifests/xrd.yaml
kubectl apply -f manifests/composition.yaml
kubectl get xrd xwebapps.platform.acme.io
```
✅ Expected: `ESTABLISHED=True`.

## Part C — Render it offline first

Before applying anything, see what the composition produces:

```bash
crossplane render manifests/xr-app.yaml manifests/composition.yaml \
  manifests/render/functions.yaml | grep '^kind:'
```
✅ Expected:
```
kind: Instance
kind: Bucket
kind: BucketPublicAccessBlock
kind: Deployment
kind: Service
kind: Ingress
```

**Six resources — three AWS, three Kubernetes — from one composition.** That mix in a
single composition is what Crossplane v1 could not do.

Now render the minimal one:
```bash
crossplane render manifests/xr-minimal.yaml manifests/composition.yaml \
  manifests/render/functions.yaml | grep '^kind:'
```
✅ Expected: only `Deployment` and `Service`. The conditionals dropped everything else.

## Part D — Apply it

```bash
kubectl apply -f manifests/xr-app.yaml
kubectl get xwebapps -n team-payments -w        # Ctrl-C when READY is True
```
✅ Expected, within 2–3 minutes:
```
NAME       IMAGE                       SIZE    DB     READY
payments   xp-course/sample-app:1.0    small   true   True
```

```bash
crossplane trace xwebapp payments -n team-payments
```
✅ Expected — the full tree, cloud and cluster resources side by side:
```
NAME                                       SYNCED   READY   STATUS
XWebApp/payments (team-payments)           True     True    Available
├─ Instance/team-payments-payments         True     True    Available
├─ Bucket/payments-bucket-...              True     True    Available
├─ BucketPublicAccessBlock/...             True     True    Available
├─ Deployment/payments                     True     True    Available
├─ Service/payments                        True     True    Available
└─ Ingress/payments                        True     True    Available
```

Confirm the Kubernetes side really exists as ordinary objects:
```bash
kubectl get deploy,svc,ingress -n team-payments
kubectl get pods -n team-payments
```
✅ Expected: 2 running pods, a Service, and an Ingress — indistinguishable from
anything you'd have written by hand.

## Part E — The point of the whole module

Look at the connection Secret the database wrote:

```bash
kubectl get secrets -n team-payments
kubectl get secret payments-db-conn -n team-payments -o jsonpath='{.data}' | jq 'keys'
```
✅ Expected:
```json
["attribute.address", "endpoint", "password", "port", "username"]
```

**Nobody created that Secret.** The RDS instance generated a password and wrote it
there, because the composition said `writeConnectionSecretToRef`.

Now confirm the app received it — **without printing the password**:
```bash
kubectl port-forward -n team-payments svc/payments 8080:80 &
sleep 3
curl -s localhost:8080/ | jq
kill %1
```
✅ Expected:
```json
{
  "app": "payments",
  "database": {
    "configured": true,
    "host": "team-payments-payments.xxxxx.us-east-1.rds.amazonaws.com",
    "password_present": true,
    "password_length": 20,
    "port": "5432",
    "user": "appuser"
  },
  "storage": { "bucket": "team-payments-payments-data" },
  "served_by": "payments-6d4f8b9c4d-x2k9p"
}
```

**`password_present: true`, and at no point did the value appear** — not in your
terminal, not in a git repo, not in a CI log, not in a state file. It was generated
by the provider, written to etcd, and mounted into the Pod by the kubelet.

Trace the whole chain to convince yourself:
```bash
# The Deployment references the Secret; it does not contain the value
kubectl get deploy payments -n team-payments \
  -o jsonpath='{.spec.template.spec.containers[0].env}' | jq '.[] | select(.name=="DB_PASSWORD")'
```
✅ Expected: a `secretKeyRef`, not a literal:
```json
{ "name": "DB_PASSWORD", "valueFrom": { "secretKeyRef": { "key": "password", "name": "payments-db-conn" } } }
```

> **This is the seam from Module 01, deleted.** Not automated with a fourth system —
> deleted, because the two halves were never in separate systems to begin with.

## Part F — Change one field, watch the stack adapt

```bash
kubectl patch xwebapp payments -n team-payments --type=merge \
  -p '{"spec":{"replicas":4,"size":"medium"}}'
sleep 30
kubectl get pods -n team-payments
kubectl get instance -o custom-columns=NAME:.metadata.name,CLASS:.spec.forProvider.instanceClass
```
✅ Expected: 4 pods, and the RDS instance class now `db.t3.small`.

**One patch changed both the Kubernetes workload and the cloud database.** Two
systems, one declaration, one reconcile loop.

## Part G — Kubernetes garbage collection does the cleanup

```bash
kubectl get deploy payments -n team-payments -o jsonpath='{.metadata.ownerReferences}' | jq
```
✅ Expected: an owner reference pointing at the `XWebApp`.

That's why deletion cascades correctly — it's ordinary Kubernetes GC, not something
Crossplane invented:
```bash
kubectl apply -f manifests/xr-minimal.yaml
sleep 45
crossplane trace xwebapp static-api -n team-payments
kubectl get deploy -n team-payments
```
✅ Expected: `static-api` produced only a Deployment and a Service — no database, no
bucket, no Ingress.

## Part H — Sequencing, and why you usually shouldn't

Try forcing the app to wait for the database at the *composition* level:

```bash
kubectl apply -f - <<'YAML'
apiVersion: apiextensions.crossplane.io/v1
kind: Composition
metadata:
  name: xwebapp-sequenced
spec:
  compositeTypeRef:
    apiVersion: platform.acme.io/v1alpha1
    kind: XWebApp
  mode: Pipeline
  pipeline:
    - step: render
      functionRef: { name: function-go-templating }
      input:
        apiVersion: gotemplating.fn.crossplane.io/v1beta1
        kind: GoTemplate
        source: Inline
        inline:
          template: |
            {{- $xr := .observed.composite.resource -}}
            ---
            apiVersion: s3.aws.upbound.io/v1beta1
            kind: Bucket
            metadata:
              annotations:
                {{ setResourceNameAnnotation "database" }}
                crossplane.io/external-name: {{ $xr.metadata.name }}-seq
            spec:
              forProvider: { region: us-east-1 }
              providerConfigRef: { name: default }
            ---
            apiVersion: v1
            kind: ConfigMap
            metadata:
              annotations:
                {{ setResourceNameAnnotation "app" }}
              name: {{ $xr.metadata.name }}-seq
              namespace: {{ $xr.metadata.namespace }}
            data:
              note: "created only after the bucket is ready"
    - step: sequence
      functionRef: { name: function-sequencer }
      input:
        apiVersion: sequencer.fn.crossplane.io/v1beta1
        kind: Input
        rules:
          - sequence: [database, app]
    - step: ready
      functionRef: { name: function-auto-ready }
YAML
```

Apply an XR using it and watch the ConfigMap appear only *after* the bucket is ready:
```bash
kubectl apply -f - <<'YAML'
apiVersion: platform.acme.io/v1alpha1
kind: XWebApp
metadata: { name: seq-demo, namespace: team-payments }
spec:
  image: xp-course/sample-app:1.0
  database: false
  storage: false
  crossplane:
    compositionRef: { name: xwebapp-sequenced }
YAML
kubectl get cm -n team-payments -w      # Ctrl-C once seq-demo-seq appears
```
✅ Expected: the ConfigMap appears *after* the bucket goes Ready, not simultaneously.

**Now consider the failure mode.** If the bucket never becomes ready, the ConfigMap is
**never created at all** — so you can't inspect it, can't read its logs, and can't
tell from the app's side what went wrong. Compare with the init-container approach in
the main composition: there the Pod *exists* and its logs say
`waiting for database at ...`, which tells you exactly what it's stuck on.

> **Prefer an init container or a crash-loop over composition-level sequencing.** A
> failing thing you can inspect beats a thing that was never created. Reach for
> `function-sequencer` only when a cloud API genuinely rejects out-of-order creation.

```bash
kubectl delete xwebapp seq-demo -n team-payments
kubectl delete composition xwebapp-sequenced
```

## Part I — Clean up

```bash
kubectl delete xwebapp --all -n team-payments
sleep 45
kubectl get managed
kubectl get deploy,svc,ingress -n team-payments
awslocal s3 ls
```
✅ Expected: everything gone — cloud and cluster resources alike, from one delete.

**Leave the XRD, composition, providers, and functions installed.**

---

## What you learned
- A namespaced v2 XR composes **Kubernetes resources directly** — no
  `provider-kubernetes`, no `Object` wrapper.
- **`writeConnectionSecretToRef`** puts generated credentials in a Secret; the
  composed Deployment reads them with `secretKeyRef`. The password never becomes
  visible to a person or a pipeline.
- One field change (`size`, `replicas`) can reconfigure **both** a cloud database and
  a Kubernetes workload.
- Composed resources get **owner references**, so deletion cascades through ordinary
  Kubernetes garbage collection.
- Prefer an **init container** to `function-sequencer`: a Pod that reports what it's
  waiting for is more debuggable than a resource that was never created.

➡️ **[challenge.md](./challenge.md)** then [Module 07](../07-aws-networking/).
