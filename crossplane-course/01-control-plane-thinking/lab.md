# Lab 01 — Two Kinds of Automation, Side by Side

**You'll:** create the same S3 bucket imperatively and declaratively, then sabotage
both and watch only one heal itself. ⏱️ ~45 min.

> Prereqs: `VERIFY.md` passed. The AWS S3 provider, the `aws-creds` Secret, and the
> `default` ProviderConfig should still be installed from that smoke test.

---

## Part A — Set up a shell helper

You'll query "AWS" constantly. Define this function in your shell (it runs the real
AWS CLI in a throwaway Pod, pointed at LocalStack):

```bash
awslocal() {
  kubectl run awscli-$RANDOM --rm -i --restart=Never -q \
    --image=amazon/aws-cli:2.18.9 \
    --env=AWS_ACCESS_KEY_ID=test \
    --env=AWS_SECRET_ACCESS_KEY=test \
    --env=AWS_DEFAULT_REGION=us-east-1 \
    -- --endpoint-url=http://localstack.localstack.svc.cluster.local:4566 "$@"
}
```

Test it:
```bash
awslocal s3 ls
```
✅ Expected: no output (no buckets yet), and no error. If you get an error, LocalStack
isn't reachable — revisit `VERIFY.md` step 3.

## Part B — The imperative way

This is how infrastructure gets made when someone is in a hurry:

```bash
awslocal s3 mb s3://manual-bucket
awslocal s3 ls
```
✅ Expected:
```
make_bucket: manual-bucket
2026-01-15 10:22:41 manual-bucket
```

Done — fast, and *completely invisible* to any system. Nothing recorded that this
should exist, why, or who asked for it. Notice what you cannot do now:

```bash
kubectl get buckets
```
✅ Expected: `No resources found` — Kubernetes has no idea this bucket exists.

> This is the "someone clicked it in the console" scenario, and it's how most drift
> is born. Module 03 teaches you to **import** a bucket like this one rather than
> recreate it.

## Part C — The declarative way

Now the same bucket, as a desired-state declaration:

```bash
cd 01-control-plane-thinking
cat manifests/bucket.yaml
kubectl apply -f manifests/bucket.yaml
```

Watch it converge:
```bash
kubectl get buckets -w        # Ctrl-C once READY is True
```
✅ Expected, after 5–30 seconds:
```
NAME              SYNCED   READY   EXTERNAL-NAME     AGE
declared-bucket   True     True    declared-bucket   12s
```

Confirm from AWS's side:
```bash
awslocal s3 ls
```
✅ Expected: **both** buckets now.
```
2026-01-15 10:22:41 manual-bucket
2026-01-15 10:24:03 declared-bucket
```

Both buckets are identical in AWS. The difference is entirely in what the *cluster*
knows about them.

## Part D — The difference: sabotage them both

This is the important part of the lab. Delete both buckets **behind Crossplane's
back**, exactly as a panicking engineer would at 2 a.m.:

```bash
awslocal s3 rb s3://manual-bucket
awslocal s3 rb s3://declared-bucket
awslocal s3 ls
```
✅ Expected: both gone.
```
remove_bucket: manual-bucket
remove_bucket: declared-bucket
```

Now wait. Crossplane polls on an interval (default ~60s), so give it a minute:

```bash
sleep 70
awslocal s3 ls
```
✅ Expected: **`declared-bucket` is back. `manual-bucket` is not.**
```
2026-01-15 10:26:15 declared-bucket
```

🎉 **You just watched drift correction happen.** Nobody ran a pipeline. Nobody
approved anything. The controller observed that reality didn't match the declaration
and fixed it.

See the recovery in the object's own history:
```bash
kubectl describe bucket declared-bucket | tail -20
```
✅ Expected: Events showing the resource being observed as missing and re-created.

> **Contrast with Terraform:** the equivalent would be a `terraform plan` — *the next
> time someone ran it* — showing `1 to add`. Between the deletion and that run, your
> infrastructure is silently wrong and nothing tells you.

## Part E — See what the cluster knows

Because the bucket is a Kubernetes object, every tool you already have works on it:

```bash
kubectl get bucket declared-bucket -o yaml | head -40
```
Read the four sections:
- `metadata.annotations."crossplane.io/external-name"` — its real identity in AWS
- `spec.forProvider` — what **you** asked for
- `status.atProvider` — what **AWS says it is** right now
- `status.conditions` — `Synced` (did the call work?) and `Ready` (does it exist?)

```bash
kubectl get bucket declared-bucket \
  -o jsonpath='{range .status.conditions[*]}{.type}={.status}  {.reason}{"\n"}{end}'
```
✅ Expected:
```
Ready=True  Available
Synced=True  ReconcileSuccess
```

And the things you get purely because it's a Kubernetes object:
```bash
kubectl label bucket declared-bucket team=platform      # labels
kubectl get buckets -l team=platform                     # selectors
kubectl auth can-i delete buckets                        # RBAC
kubectl get events --field-selector involvedObject.name=declared-bucket
```
✅ Expected: all four work, with no special tooling. **This is the "free stuff"
argument from the README, made concrete.**

## Part F — Pause the loop

Sometimes you need Crossplane to stop touching a resource while you investigate.
That's what the pause annotation is for:

```bash
kubectl annotate bucket declared-bucket crossplane.io/paused=true
awslocal s3 rb s3://declared-bucket
sleep 70
awslocal s3 ls
```
✅ Expected: the bucket stays deleted. Crossplane is no longer reconciling it.

```bash
kubectl get bucket declared-bucket
```
✅ Expected: `SYNCED` is now blank or `False` — the controller has stopped.

Resume it:
```bash
kubectl annotate bucket declared-bucket crossplane.io/paused-
sleep 70
awslocal s3 ls
```
✅ Expected: the bucket is recreated. The loop is running again.

> **Remember this annotation.** It's the emergency brake, and it will save you when a
> composition starts doing something you didn't intend at exactly the wrong moment.

## Part G — Clean up

```bash
kubectl delete -f manifests/bucket.yaml
kubectl wait --for=delete bucket/declared-bucket --timeout=2m
awslocal s3 ls
```
✅ Expected: no buckets at all. Deleting the Kubernetes object deleted the real
resource — because `deletionPolicy` defaults to `Delete`. Module 03 covers when you
very much want the other option.

---

## What you learned
- A **provisioning tool** acts when run; a **control plane** acts continuously.
- Drift is **corrected**, not merely reported — you watched a deleted bucket return.
- Making cloud resources into Kubernetes objects gives you labels, selectors, RBAC,
  events, and `kubectl` for free.
- `crossplane.io/paused=true` stops the loop for one resource without deleting it.
- `SYNCED` means "the API call worked"; `READY` means "the resource exists and works".

➡️ **[challenge.md](./challenge.md)** then [Module 02](../02-providers-and-managed-resources/).
