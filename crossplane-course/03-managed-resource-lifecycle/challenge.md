# Challenge 03 — Adopt a Messy Estate

Solutions in [`solutions/`](./solutions/). Try first.

You've joined a company with infrastructure nobody documented. Your job is to bring it
under management without breaking anything.

## Setup

Create the mess (run this first):

```bash
awslocal s3 mb s3://acme-prod-uploads
awslocal s3 mb s3://acme-prod-backups
awslocal s3 mb s3://acme-staging-uploads
awslocal s3api put-bucket-versioning --bucket acme-prod-backups \
  --versioning-configuration Status=Enabled
awslocal s3api put-bucket-tagging --bucket acme-prod-uploads \
  --tagging 'TagSet=[{Key=env,Value=prod},{Key=team,Value=payments}]'
kubectl run seed --rm -i --restart=Never -q --image=amazon/aws-cli:2.18.9 \
  --env=AWS_ACCESS_KEY_ID=test --env=AWS_SECRET_ACCESS_KEY=test \
  --env=AWS_DEFAULT_REGION=us-east-1 --command -- sh -c \
  'echo backup-data | aws --endpoint-url=http://localstack.localstack.svc.cluster.local:4566 s3 cp - s3://acme-prod-backups/jan.bak'
```

## Tasks

1. **Audit before you touch.** Import all three buckets in **read-only** mode. Do not
   guess at their configuration — write manifests with only the minimum needed, let
   Crossplane observe, then produce a short written inventory of what each bucket
   actually is: its tags, whether versioning is on, and whether it holds data. Use
   only `kubectl` against your imported objects for the inventory, not `awslocal`.

2. **Adopt with the right risk posture.** Now take full management of all three, but
   with settings appropriate to each:
   - `acme-prod-backups` holds data and must be impossible to destroy accidentally.
   - `acme-prod-uploads` must keep its existing tags exactly — importing must not
     change them.
   - `acme-staging-uploads` is disposable and should be fully managed with defaults.

   Prove after applying that no bucket's real configuration changed. That is the
   whole test: a successful import is one nothing notices.

3. **Prove your protection works.** Delete all three Kubernetes objects. Show that
   `acme-prod-backups` still exists in AWS with its data intact, and that
   `acme-staging-uploads` is genuinely gone. Explain in one sentence which setting
   produced each outcome.

4. **The dangerous scenario.** A colleague proposes this to "clean up drift":
   ```bash
   kubectl get buckets -o name | xargs kubectl delete
   ```
   Explain precisely what would happen in your imported estate, which buckets survive,
   and why. Then write the guardrail you'd put in place so a command like that cannot
   destroy production. (Think beyond `deletionPolicy` — Module 13 covers RBAC, but you
   can reason about it now.)

5. **Stretch — automate the import.** Write a shell script that takes a bucket name,
   generates an Observe-only manifest, applies it, waits for it to sync, and prints
   the discovered `status.atProvider` as a suggested `spec.forProvider`. This is the
   skeleton of the tooling every team building on Crossplane ends up writing.

## Success criteria
- [ ] All three buckets imported read-only first, with a written inventory derived
      from `status.atProvider`.
- [ ] All three adopted with a risk posture matched to their contents, and you proved
      nothing changed in AWS.
- [ ] Deleting the objects protected the backups bucket and destroyed the staging one,
      and you can name the setting responsible for each.
- [ ] You explained the blast radius of the mass-delete command and proposed a
      guardrail beyond `deletionPolicy`.
