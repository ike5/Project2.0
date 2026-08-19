# Challenge 06 — Reference Solution

Runnable manifests: [`xwebapp-full.yaml`](./xwebapp-full.yaml) (Tasks 1 and 2),
[`xplatform.yaml`](./xplatform.yaml) (Task 5).

---

### 1. Bucket-scoped AWS credentials

The addition to the template, inside the `{{- if $xr.spec.storage }}` block:

```gotemplate
---
apiVersion: iam.aws.upbound.io/v1beta1
kind: User
metadata:
  annotations:
    {{ setResourceNameAnnotation "app-user" }}
    crossplane.io/external-name: {{ printf "%s-%s-app" $ns $name }}
spec:
  forProvider: {}
  providerConfigRef: { name: default }
---
apiVersion: iam.aws.upbound.io/v1beta1
kind: UserPolicy
metadata:
  annotations:
    {{ setResourceNameAnnotation "app-user-policy" }}
spec:
  forProvider:
    userRef:
      name: {{ printf "%s-app-user" $name }}
    policy: |
      {
        "Version": "2012-10-17",
        "Statement": [{
          "Effect": "Allow",
          "Action": ["s3:GetObject","s3:PutObject","s3:DeleteObject"],
          "Resource": "arn:aws:s3:::{{ printf "%s-%s-data" $ns $name }}/*"
        },{
          "Effect": "Allow",
          "Action": ["s3:ListBucket"],
          "Resource": "arn:aws:s3:::{{ printf "%s-%s-data" $ns $name }}"
        }]
      }
  providerConfigRef: { name: default }
---
apiVersion: iam.aws.upbound.io/v1beta1
kind: AccessKey
metadata:
  annotations:
    {{ setResourceNameAnnotation "app-access-key" }}
spec:
  forProvider:
    userRef:
      name: {{ printf "%s-app-user" $name }}
  providerConfigRef: { name: default }
  writeConnectionSecretToRef:
    namespace: {{ $ns }}
    name: {{ printf "%s-aws-creds" $name }}
```

Injected the same way the database password was:
```gotemplate
- name: AWS_ACCESS_KEY_ID
  valueFrom:
    secretKeyRef: { name: {{ printf "%s-aws-creds" $name }}, key: username }
- name: AWS_SECRET_ACCESS_KEY
  valueFrom:
    secretKeyRef: { name: {{ printf "%s-aws-creds" $name }}, key: password }
```

Note the policy scopes to **this bucket only**, and needs two statements: object
actions on `bucket/*` and `ListBucket` on `bucket` itself. Granting `s3:*` on `*`
is the mistake this pattern exists to prevent.

**Why an IAM user is the wrong long-term answer:**

1. **The key is long-lived and never rotates.** It sits in etcd and in the Pod's
   environment indefinitely. If it leaks, it's valid until someone notices.
2. **It doesn't rotate on Pod restart, redeploy, or team change.** Compare with a
   database password, which at least you could rotate by recreating the resource.
3. **It's an identity outside Kubernetes' control.** Kubernetes RBAC says nothing
   about it; audit trails show `payments-app` did something, not which Pod or which
   deployment.
4. **It scales badly.** 40 services means 40 IAM users, 40 access keys, and a
   rotation problem nobody owns.

**What you'd use on real EKS: IRSA** (IAM Roles for Service Accounts). The
composition would create an IAM `Role` whose trust policy accepts the cluster's OIDC
provider for a specific ServiceAccount, and a ServiceAccount annotated with that
role's ARN. The Pod then receives **short-lived, automatically rotated** credentials
from STS, and there is no key to leak. Module 08 builds exactly this.

### 2. The worker

Schema:
```yaml
worker:
  type: object
  properties:
    enabled: { type: boolean, default: false }
    replicas: { type: integer, default: 1, minimum: 1, maximum: 20 }
    command: { type: array, items: { type: string } }
```

Template — a second Deployment sharing the same connection secret:
```gotemplate
{{- if and $xr.spec.worker $xr.spec.worker.enabled }}
---
apiVersion: apps/v1
kind: Deployment
metadata:
  annotations:
    {{ setResourceNameAnnotation "worker" }}
  name: {{ printf "%s-worker" $name }}
  namespace: {{ $ns }}
spec:
  replicas: {{ $xr.spec.worker.replicas | default 1 }}
  selector:
    matchLabels:
      app: {{ printf "%s-worker" $name }}
  template:
    metadata:
      labels:
        app: {{ printf "%s-worker" $name }}
    spec:
      containers:
        - name: worker
          image: {{ $xr.spec.image }}
          command: {{ toYaml ($xr.spec.worker.command | default (list "python" "worker.py")) | nindent 12 }}
          env:
            {{- if $xr.spec.database }}
            - name: DB_HOST
              valueFrom:
                secretKeyRef: { name: {{ $connSecret }}, key: endpoint }
            - name: DB_PASSWORD
              valueFrom:
                secretKeyRef: { name: {{ $connSecret }}, key: password }
            {{- end }}
{{- end }}
```

Note `{{- if and $xr.spec.worker $xr.spec.worker.enabled }}`: checking the parent
object exists before reading a child field. Without the `and`, an XR that omits
`worker` entirely produces a nil-map error and the whole render fails — the same
class of bug as the unguarded lookups in Module 05.

Independent scaling works because they are two separate Deployments with separate
`replicas`, both driven from the XR.

### 3. Deleting the connection secret

```bash
kubectl delete secret payments-db-conn -n team-payments
```

**Observations:**

**a) Running Pods: nothing happens, immediately or ever.** Environment variables from
`secretKeyRef` are resolved **once, at container start**. The values are already in
the process's environment. The app keeps working indefinitely. This surprises most
people and is worth internalising.

**b) New Pods: they fail to start.**
```bash
kubectl delete pod -n team-payments -l app=payments
kubectl get pods -n team-payments
# STATUS: CreateContainerConfigError
kubectl describe pod -n team-payments -l app=payments | tail -5
# Error: secret "payments-db-conn" not found
```

**c) Crossplane recreates it — within one reconcile interval (up to ~60s).** The RDS
managed resource still declares `writeConnectionSecretToRef`, so the provider rewrites
the Secret with the same values on its next pass. **This is drift correction applied
to a Kubernetes object rather than a cloud one**, and it's a nice demonstration that
the same loop covers both.

**d) What a developer sees:** a latent time bomb. Everything looks healthy — the XR is
`Ready`, the app is serving traffic — until the next deploy, node drain, or scale-up,
at which point pods fail with `CreateContainerConfigError`. If the Secret gets
recreated before then, the incident never happens and nobody learns anything. If it
doesn't, the failure appears hours later with no obvious link to its cause.

**Improvement:** mount the Secret as a **projected volume** rather than environment
variables:
```yaml
volumes:
  - name: db-creds
    secret: { secretName: payments-db-conn }
```
The kubelet then tracks the Secret continuously and updates the mounted files, so
deletion is visible to a running Pod rather than latent. Combine with a readiness
probe that actually checks the database connection, and the failure surfaces as an
unready Pod within seconds instead of at the next restart.

> The general lesson: **`secretKeyRef` env vars are a point-in-time snapshot.** For
> anything you might rotate, mount it.

### 4. Why the VPC does not belong in XWebApp

**Apply the lifecycle test from the README: should deleting the app delete the
network?** Obviously not. That single question settles it, but the concrete failures
are worth naming:

1. **Cost and limits.** AWS defaults to **5 VPCs per region per account**. Forty apps
   means forty VPCs — you'd hit the quota at app number six. Each VPC needing internet
   access also needs a NAT Gateway at roughly $32/month plus data charges, so this
   design costs over $1,200/month in NAT alone for nothing.
2. **Nothing can talk to anything.** Apps in separate VPCs can't reach each other
   without peering or Transit Gateway. You'd be rebuilding your entire service mesh as
   network plumbing, and the peering mesh grows as O(n²).
3. **Deletion becomes dangerous.** The VPC is created by whichever app happened to be
   first; deleting *that* app tries to delete the VPC, which fails with
   `DependencyViolation` — or worse, succeeds and takes everything down.
4. **Provisioning gets slow.** A VPC with subnets, gateways, and route tables takes
   minutes. Every app deploy would pay that cost to recreate infrastructure that
   already exists.

**What to do instead:** the VPC is **platform-owned, long-lived infrastructure**, on a
completely different lifecycle from any app. Provision it once (a separate `XNetwork`
XR, or Terraform — Module 01's memo argues Terraform is a fine choice for exactly this
layer), then expose its IDs to app compositions through an **EnvironmentConfig**
(Module 10):

```yaml
apiVersion: apiextensions.crossplane.io/v1beta1
kind: EnvironmentConfig
metadata:
  name: aws-network-prod
data:
  vpcId: vpc-0abc123
  privateSubnetIds: ["subnet-01", "subnet-02"]
```

Apps *reference* the network; they don't *own* it. **Ownership follows lifecycle.**

### 5. Stretch — XPlatform, and its danger

See [`xplatform.yaml`](./xplatform.yaml). The mechanic is that composed resources can
be XRs:

```gotemplate
---
apiVersion: platform.acme.io/v1alpha1
kind: XWebApp
metadata:
  annotations:
    {{ setResourceNameAnnotation "frontend" }}
  name: {{ printf "%s-frontend" $name }}
  namespace: {{ $ns }}
spec:
  image: {{ $xr.spec.frontendImage }}
  database: false
  storage: false
```

**What makes it powerful:** genuine abstraction layering. A team gets a whole
environment from one resource, and the `XWebApp` API is reused rather than
copy-pasted. Improve `XWebApp` once and every platform benefits. This is how large
platform teams keep dozens of APIs coherent.

**What makes it dangerous:** deleting the `XPlatform` deletes all three apps **and
their databases**, through ordinary owner-reference cascade. One `kubectl delete` on
one object destroys an entire environment, and the object's name gives no hint of its
blast radius.

Worse, the cascade is *invisible in review*. A pull request removing a 12-line
`XPlatform` file looks trivial. Its actual effect is deleting three Deployments, three
databases, and a bucket.

**Mitigations, in order of importance:**
1. **`deletionPolicy: Orphan`** on every stateful composed resource, so data survives
   even a full cascade.
2. **RBAC**: almost nobody should hold `delete` on `xplatforms`.
3. **A validating admission policy** blocking deletion of XRs labelled
   `criticality: high`.
4. **Keep nesting shallow.** Two levels is comprehensible; three is not. If you can't
   predict what a delete does, the abstraction is too deep.

This is the same lesson as Module 04's composition-selector danger, in a new costume:
**in a control plane, deletion is an action with a blast radius, and the size of the
YAML tells you nothing about the size of the blast.**
