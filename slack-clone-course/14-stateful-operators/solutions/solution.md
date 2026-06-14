# Challenge 14 — Reference Solution

### 1. Scheduled backups to MinIO
```yaml
# add to the Cluster spec
spec:
  backup:
    barmanObjectStore:
      destinationPath: s3://slack-backups/
      endpointURL: http://minio:9000
      s3Credentials:
        accessKeyId: {name: backend-secret, key: S3_ACCESS_KEY}
        secretAccessKey: {name: backend-secret, key: S3_SECRET_KEY}
    retentionPolicy: "7d"
---
apiVersion: postgresql.cnpg.io/v1
kind: ScheduledBackup
metadata: {name: nightly, namespace: slack}
spec:
  schedule: "0 0 2 * * *"     # 02:00 daily (6-field cron)
  cluster: {name: slack-pg}
```
On-demand: `kubectl cnpg backup slack-pg -n slack`, then check the `slack-backups` bucket.

### 2. Measure the failover window
```bash
while true; do
  curl -s -o /dev/null -w "%{http_code} %{time_total}\n" -H "Authorization: Bearer $ACCESS" \
    -H 'content-type: application/json' -X POST slack.local/api/messages/ \
    -d "{\"channel\":$CH,\"body\":\"hb $(date +%s)\"}"
  sleep 1
done
# in another shell: kubectl delete pod $(kubectl get cluster slack-pg -n slack -o jsonpath='{.status.currentPrimary}') -n slack
```
> You'll see a handful of `5xx`/timeouts for a few seconds while the replica is
> promoted and `-rw` repoints, then `201`s resume — no manual action.

### 3. Reads on replicas
> Queries that tolerate slightly stale data — analytics, admin reports, search over old
> history — can target `slack-pg-ro`. But **chat reads right after a write** (you post a
> message and immediately reload) need **read-your-writes** consistency; a replica may
> lag behind the primary by milliseconds-to-seconds, so the just-written row might be
> missing. Routing those to the primary avoids confusing "my message vanished" bugs.

### 4. Redis failover
> Deleting the Redis master briefly disrupts the channel layer; in-flight broadcasts
> during the gap may be lost (the channel layer is not a durable queue), but once
> Sentinel promotes a new master, new messages flow again and clients reconnect. Durable
> data (messages) is safe in Postgres; only the *ephemeral* live delivery blips.

### 5. HA vs backups
> - **HA saves you** when a node/pod dies: failover keeps the service up, no data lost.
> - **Backups save you** when data is *corrupted or wrongly deleted* — a bad migration,
>   an accidental `DELETE FROM messages`: HA faithfully replicates the bad change to
>   every replica, so only a restore from before the mistake recovers it.
> - **You need both** when a node dies *and* you later discover the last deploy had a
>   data-destroying bug: HA kept you online; PITR backups roll the data back to before
>   the bug.
