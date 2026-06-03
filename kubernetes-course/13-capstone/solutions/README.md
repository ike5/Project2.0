# Capstone — Reference Solution

A complete, applyable implementation of the guestbook capstone. Try building it
yourself first ([../README.md](../README.md)); use this to check yourself or unblock.

## Files (apply in this order)
| File | What it creates |
|------|-----------------|
| `00-namespace.yaml` | `guestbook` namespace |
| `10-secret.yaml` | `redis-auth` Secret (shared password) |
| `11-configmap.yaml` | `guestbook-config` (PAGE_TITLE) |
| `20-redis.yaml` | Redis **StatefulSet** + PVC + Service (password-protected) |
| `30-guestbook.yaml` | guestbook **Deployment** (2 replicas, probes, resources) + Service |
| `31-ingress.yaml` | Ingress at `http://localhost/` |
| `32-hpa.yaml` | HPA (CPU 60%, 2–10 replicas) |
| `40-networkpolicy.yaml` | only guestbook may reach Redis:6379 |

## Quick deploy
```bash
# prereqs: cluster up; ingress-nginx (Module 05) + metrics-server (Module 08) installed
./deploy-all.sh
open http://localhost/        # macOS; or just visit in a browser
```

Or manually:
```bash
cd apps/guestbook && docker build -t guestbook:1.0 . && \
  kind load docker-image guestbook:1.0 --name k8s-course && cd -
kubectl apply -f 13-capstone/solutions/
kubectl rollout status statefulset/redis -n guestbook
kubectl rollout status deployment/guestbook -n guestbook
```

## Verify (acceptance test)
```bash
curl -s -XPOST http://localhost/api/messages \
  -H 'Content-Type: application/json' -d '{"text":"hello capstone"}'
curl -s http://localhost/api/messages          # includes your message

# persistence across Redis restart:
kubectl delete pod redis-0 -n guestbook
kubectl wait --for=condition=Ready pod/redis-0 -n guestbook --timeout=120s
curl -s http://localhost/api/messages          # message still present

# autoscaling (generate load):
kubectl run loader -n guestbook --image=busybox:1.36 --restart=Never -- \
  sh -c 'while true; do wget -q -O- http://guestbook/api/messages >/dev/null; done'
kubectl get hpa guestbook -n guestbook -w       # replicas climb; Ctrl+C
kubectl delete pod loader -n guestbook
```

## NetworkPolicy check (Calico cluster only)
```bash
# a random pod should NOT reach redis; a guestbook-labeled pod should.
kubectl run probe -n guestbook --rm -it --image=busybox:1.36 --restart=Never -- \
  sh -c 'nc -zvw2 redis 6379'                    # denied on Calico, allowed on kindnet
```

## Teardown
```bash
kubectl delete -f 13-capstone/solutions/ --ignore-not-found
kubectl delete pvc -n guestbook -l app=redis     # StatefulSet PVCs aren't auto-deleted
```

## Bonus: package it
- **Helm/Kustomize** (Module 10): convert these manifests into a chart or a
  base+overlays so you can parameterize the page title, replicas, and image tag.
- **GitOps** (Module 12): push to your repo and create an Argo CD Application
  pointing at `13-capstone/solutions/` so the cluster syncs from Git.
