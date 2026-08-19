# Troubleshooting: "My Stack Is Stuck" Decision Tree

Crossplane almost always tells you what's wrong. The trick is knowing which of the
**four layers** to look at. Start at the top, every time.

```
Layer 1  Your XR            → is the composition even rendering?
Layer 2  Composed resources → did the composition produce what you expected?
Layer 3  The provider       → did the cloud API accept the call?
Layer 4  The cloud          → does the resource actually work?
```

**The single command that spans all four:**
```bash
crossplane trace <kind> <name> -n <namespace>
```
Read it top-down and stop at the first thing that isn't `True`.

---

## The two conditions, and what they mean

Every Crossplane resource carries these. Learn to read them as a pair:

| `SYNCED` | `READY` | Meaning | Where to look |
|----------|---------|---------|---------------|
| `True` | `True` | Working. | — |
| `True` | `False` | The API call worked; the resource is still coming up (or is unhealthy). | Normal for 30s–10min on RDS/VPC. If stuck: `describe` the resource. |
| `False` | `False` | **The API call itself failed.** This is the common case. | The `Synced` condition's `message` — it contains the raw cloud error. |
| `False` | `True` | Was working; a later update was rejected. | The `Synced` message. Your spec change is invalid. |
| *(no conditions at all)* | | Nothing is reconciling it. | Is the provider `Healthy`? Is the resource `paused`? |

```bash
kubectl get bucket my-bucket -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'
```

---

## Layer 1 — The XR isn't producing resources

### Symptom: XR exists, but `crossplane trace` shows no children

```bash
kubectl describe xdatabase my-db -n team-a     # Events at the bottom
kubectl logs -n crossplane-system deploy/crossplane --tail=50
```

- **"no composition selected" / `CompositionSelectionFailed`** → No Composition's
  `compositeTypeRef` matches your XRD's group/version/kind. They must match
  **exactly**, including the API version. This is the #1 beginner error.
- **"cannot find composition"** → Your `compositionRef.name` names a Composition that
  doesn't exist. Check spelling: `kubectl get compositions`.
- **Multiple compositions match, none chosen** → Add a `compositionSelector` with
  labels, or name one explicitly with `compositionRef`.
- **Nothing in the logs at all** → The XRD may not have established. Check:
  ```bash
  kubectl get xrd
  # ESTABLISHED must be True; OFFERED matters only for LegacyCluster scope
  ```

### Symptom: `no matches for kind "XDatabase"`

The XRD hasn't created its CRD yet, or you got the plural/group wrong.
```bash
kubectl get xrd xdatabases.platform.example.org -o yaml | grep -A5 conditions
kubectl api-resources --api-group=platform.example.org
```

---

## Layer 2 — The composition renders the wrong thing

**Debug this offline. Don't guess against a live cluster:**

```bash
crossplane render xr.yaml composition.yaml functions.yaml
```

- **A field is empty that should have a value** → the patch's `fromFieldPath` doesn't
  exist on the XR. Paths are silently skipped unless you set
  `policy: { fromFieldPath: Required }`. **Add that while developing** — it turns a
  silent bug into a loud error.
- **`function failed: ...` in the XR events** → read the function's own logs:
  ```bash
  kubectl logs -n crossplane-system -l pkg.crossplane.io/function=function-patch-and-transform
  ```
- **Resources appear then vanish** → two composed resources share a `name` in the
  composition, so one overwrites the other. Every entry needs a unique name.
- **Go template renders nothing** → a `{{ if }}` you thought was true isn't. Print the
  context to check:
  ```gotemplate
  {{ toYaml .observed.composite.resource.spec }}
  ```

---

## Layer 3 — The provider rejects the call (`SYNCED=False`)

```bash
kubectl describe bucket my-bucket        # Events carry the AWS error verbatim
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=provider-aws-s3 --tail=100
```

| Error text | Cause | Fix |
|------------|-------|-----|
| `InvalidClientTokenId`, `SignatureDoesNotMatch` | Bad or malformed credentials | The Secret's key must be INI format, `[default]` line included |
| `no such host`, `connection refused` | Endpoint unreachable | Check the `ProviderConfig` endpoint URL; from a Pod, curl the emulator health path |
| `AccessDenied`, `UnauthorizedOperation` | Real IAM problem | The role/user lacks the action. Read which action the message names |
| `cannot find ProviderConfig` | Typo'd or missing `providerConfigRef` | `kubectl get providerconfigs` |
| `ValidationError`, `InvalidParameterValue` | Your `forProvider` is wrong | The message names the field. Check the provider's CRD: `kubectl explain bucket.spec.forProvider` |
| `BucketAlreadyExists` | S3 names are globally unique | Add a suffix. Real AWS is far stricter than the emulator here |
| `DependencyViolation` | Deleting something still in use | Delete children first, or use `Usage` to order it (Module 10) |

### The provider itself is unhealthy

```bash
kubectl get providers
kubectl describe provider provider-aws-s3
kubectl get pods -n crossplane-system
```
- **`Healthy=False`, image pull errors** → registry unreachable or a bad tag.
- **Provider pod `OOMKilled`** → too many CRDs activated. This is exactly what
  **MRAP** solves (Module 02): activate only the resources you use.
- **`no matches for kind` right after installing** → CRD installation is still in
  flight. Wait for `Healthy=True`.

---

## Layer 4 — Ask the cloud directly

Never trust one side's story. Check the other:

```bash
awslocal s3 ls
awslocal ec2 describe-vpcs
awslocal rds describe-db-instances
```
(The `awslocal` function is in [crossplane-cli.md](./crossplane-cli.md).)

- **Crossplane says Ready, AWS doesn't have it** → you're pointed at a different
  account/region/endpoint than you think.
- **AWS has it, Crossplane says not synced** → likely an external-name mismatch;
  Crossplane is looking for a differently-named resource (Module 03).

---

## Deletion problems

### Stuck `Terminating` forever

```bash
kubectl get bucket my-bucket -o jsonpath='{.metadata.finalizers}'
kubectl describe bucket my-bucket        # Events say WHY the cloud refuses
```

Order of attack:
1. **Read the error.** `BucketNotEmpty`, `DependencyViolation` — the cloud is telling
   you exactly what's blocking. Fix that.
2. **Is the provider even running?** A deleted provider means nobody is left to
   process the finalizer. Reinstall it and deletion completes on its own.
3. **Only then**, and knowing it orphans the cloud resource:
   ```bash
   kubectl patch bucket my-bucket --type=merge -p '{"metadata":{"finalizers":[]}}'
   ```

### Deleted the XR, resources are still in AWS

Expected if `deletionPolicy: Orphan` or `managementPolicies` excludes `Delete`.
Otherwise, check whether the provider was healthy at deletion time.

### Deleting the whole cluster deleted my real infrastructure 😱

`kind delete cluster` on a cluster pointed at **real AWS** does **not** delete your
AWS resources — the controllers just stop, and the cloud resources are orphaned. It's
`kubectl delete` on the objects that destroys them. Set `deletionPolicy: Orphan` on
anything you can't afford to lose, and see Module 13.

---

## "It was working yesterday"

```bash
# Did a composition change and auto-roll to every XR?
kubectl get compositionrevisions

# Did a provider auto-upgrade?
kubectl get providerrevisions
```
Both are the usual culprits, and both are Module 11's subject. The fix is pinning:
`compositionUpdatePolicy: Manual` and explicit package tags (never `:latest`).

---

## Nuclear options, in increasing order of violence

```bash
# 1. Pause one resource so Crossplane stops fighting you
kubectl annotate bucket my-bucket crossplane.io/paused=true

# 2. Force one reconcile without changing anything meaningful
kubectl annotate bucket my-bucket reconcile-trigger="$(date +%s)" --overwrite

# 3. Restart a provider
kubectl rollout restart deploy -n crossplane-system \
  -l pkg.crossplane.io/provider=provider-aws-s3

# 4. Reset "AWS" entirely — instant clean slate
kubectl rollout restart deploy/moto -n aws-local

# 5. Burn it down (all state is in git, so this is cheap)
00-setup/scripts/delete-cluster.sh && 00-setup/scripts/create-cluster.sh
```
