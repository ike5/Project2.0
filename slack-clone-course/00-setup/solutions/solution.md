# Challenge 00 — Reference Solution

### 1. Create a table by hand
```bash
docker compose -f compose.dev.yml exec postgres psql -U slack -d slack
```
```sql
CREATE TABLE ping (id serial primary key, note text);
INSERT INTO ping (note) VALUES ('hello');
SELECT * FROM ping;       -- 1 | hello
DROP TABLE ping;
\q
```

### 2. Make Redis forget
```bash
docker compose -f compose.dev.yml exec redis redis-cli
```
```
SET flash hi EX 10     -> OK     # EX 10 sets a 10-second TTL in one command
GET flash              -> "hi"
# wait 11 seconds…
GET flash              -> (nil)  # the key expired and was removed
```

### 3. Survive a restart
```bash
docker compose -f compose.dev.yml stop postgres
docker compose -f compose.dev.yml start postgres
docker compose -f compose.dev.yml exec postgres psql -U slack -d slack -c '\l'
# the "slack" database is still listed
```
> The data survived because Postgres writes to the named volume `pgdata`, which is
> stored on your host and outlives the container — only the *process* restarted,
> not the storage.

### 4. Inspect the cluster
```bash
./scripts/create-cluster.sh
kubectl get nodes        # 3 nodes: slack-control-plane (control-plane) + 2 workers
kubectl get pods -A      # system Pods (coredns, kube-proxy, etc.) across the nodes
```
- **3 nodes.** `slack-control-plane` is the control-plane; `slack-worker` and
  `slack-worker2` are workers.
- `kubectl get pods -A` (the `-A` = all namespaces) lists the system Pods.

### 5. The gotcha, explained
> The script first runs `kind get clusters | grep -qx slack`; if the cluster
> already exists it prints a message and skips creation instead of erroring. That
> makes it **idempotent** — safe to run at the start of every session without
> worrying about whether the cluster is already up.
