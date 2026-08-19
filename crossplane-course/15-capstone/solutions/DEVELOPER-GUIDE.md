# Shipping a service on the ACME platform

For product engineers. **You do not need to know anything about AWS to use this.**

---

## Ship a service

Create a file in your team's repo under `infrastructure/`:

```yaml
apiVersion: platform.acme.io/v1alpha1
kind: Service
metadata:
  name: checkout                 # your service's name
  namespace: team-payments       # your team's namespace
  labels:
    acme.io/owner: team-payments # required — who to contact
spec:
  image: acme/checkout:2.1.0     # a pinned tag, never :latest
  size: medium                   # small | medium | large
  database: true                 # a private Postgres
  storage: true                  # a private S3 bucket
  host: checkout.acme.example    # omit for an internal-only service
```

Open a pull request. On merge, it's live in a few minutes.

## Check on it

```bash
kubectl get services.platform.acme.io -n team-payments
```
```
NAME       IMAGE                SIZE     DB     ENV   URL                          READY
checkout   acme/checkout:2.1.0  medium   true   dev   http://checkout.acme.example True
```

```bash
# The full picture, including anything that's broken
crossplane trace service.platform.acme.io checkout -n team-payments
```

## Connect to your database

**You will never be given a password, and you don't need one.** The platform injects
these environment variables into every Pod automatically:

| Variable | What it is |
|----------|-----------|
| `DATABASE_HOST` | Where the database is |
| `DATABASE_PORT` | `5432` |
| `DATABASE_USER` | `appuser` |
| `DATABASE_PASSWORD` | Generated. Never printed, logged, or shown to anyone. |
| `DATABASE_SSLMODE` | `require` |

```python
import os, psycopg

conn = psycopg.connect(
    host=os.environ["DATABASE_HOST"],
    port=os.environ["DATABASE_PORT"],
    user=os.environ["DATABASE_USER"],
    password=os.environ["DATABASE_PASSWORD"],
    sslmode=os.environ["DATABASE_SSLMODE"],
)
```

Your Pods wait for the database automatically before starting — that's the
`wait-for-db` init container you'll see in `kubectl get pods`.

## Use your bucket

`BUCKET_NAME` and `AWS_REGION` are set for you, and your Pod's identity already has
permission to use that bucket — **and only that bucket**. No keys, no configuration.

```python
import os, boto3

s3 = boto3.client("s3")                     # credentials are automatic
s3.put_object(Bucket=os.environ["BUCKET_NAME"], Key="report.csv", Body=data)
```

## Change something

Edit the file, open a pull request.

**Safe to change any time:**
- `image` — a normal rolling deploy
- `size` — **upward only** (see below)
- `minReplicas`
- `host`

**Cannot be changed after creation:**
- `database` and `storage` — turning either off would destroy your data, so the
  platform rejects it. Create a new Service instead.
- `size` **downward** — AWS cannot shrink database storage, so downsizing would mean
  replacing the database. Rejected.

If you try, you get a clear error at apply time rather than a surprise later:
```
`size` can only be increased. AWS cannot shrink allocated storage, so downsizing
would force the database to be replaced and the data lost.
```

## When something is wrong

```bash
# 1. What does the platform think?
crossplane trace service.platform.acme.io checkout -n team-payments

# 2. Your application's own logs
kubectl logs -n team-payments deploy/checkout
kubectl logs -n team-payments deploy/checkout -c wait-for-db   # stuck on the database?

# 3. What happened recently
kubectl describe service.platform.acme.io checkout -n team-payments | tail -20
```

**Reading `crossplane trace`:** find the first row that isn't `True` — that's what's
blocking you. `SYNCED=True, READY=False` on a database is **normal for a few minutes**
while AWS provisions it.

## Things you can't do, and why

| | Why |
|---|---|
| Set the AWS region, instance class, or engine version | Platform decisions. Ask us if you have a real need — that's a good conversation. |
| Create a raw `Bucket` or `Instance` | It would skip encryption, access blocking, and IAM scoping. The `Service` API is how those get guaranteed. |
| Set `environment` | It comes from your namespace. |
| Delete a production Service | Break-glass only, so it can't happen by accident. Ask in `#platform`. |

## Getting help

- `#platform` in Slack.
- Include the output of `crossplane trace` — it answers most questions immediately.
