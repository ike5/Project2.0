# Cheatsheet — kubectl, Helm & this app

For the Kubernetes fundamentals, see the
[Kubernetes course cheatsheets](../../kubernetes-course/cheatsheets/). This focuses on
operating *our* stack.

## Cluster lifecycle (kind)

```bash
00-setup/scripts/create-cluster.sh      # 1 control-plane + 2 workers
00-setup/scripts/verify-setup.sh        # 3 nodes Ready
00-setup/scripts/delete-cluster.sh
```

## Build → load → deploy (the loop)

```bash
docker build -t slack-backend:dev ./apps/slack-backend
kind load docker-image slack-backend:dev --name slack     # REQUIRED for kind
kubectl apply -k k8s/base                                 # kustomize the app
kubectl apply -f k8s/base/migrate-job.yaml                # one-shot migrations
```
`imagePullPolicy: IfNotPresent` + `kind load` → no `ImagePullBackOff`.

## Inspect

```bash
kubectl get pods -n slack -o wide        # which node each pod is on
kubectl get deploy,svc,ingress -n slack
kubectl logs -n slack deploy/web -f
kubectl logs -n slack job/migrate
kubectl describe pod -n slack <pod>      # events: why it's Pending/CrashLoop
kubectl exec -n slack -it deploy/web -- python manage.py shell
kubectl get hpa -n slack                 # autoscaler targets
```

## Operate

```bash
kubectl rollout restart deploy/web -n slack          # re-read ConfigMap/Secret
kubectl set image -n slack deploy/web web=slack-backend:v2
kubectl rollout status -n slack deploy/web
kubectl rollout undo   -n slack deploy/web
kubectl scale -n slack deploy/web --replicas=4
kubectl port-forward -n slack svc/web 8000:8000
```

## Operators (data tier)

```bash
# CloudNativePG
kubectl apply --server-side -f https://raw.githubusercontent.com/cloudnative-pg/cloudnative-pg/release-1.24/releases/cnpg-1.24.0.yaml
kubectl get cluster -n slack
kubectl get cluster slack-pg -n slack -o jsonpath='{.status.currentPrimary}'
kubectl cnpg status slack-pg -n slack          # with the cnpg kubectl plugin

# redis-operator
helm repo add redis-operator https://spotahome.github.io/redis-operator
helm install redis-operator redis-operator/redis-operator -n slack
```

## HA & failure drills

```bash
kubectl apply -f k8s/ha/hpa.yaml -f k8s/ha/pdb.yaml
kubectl patch deploy/web -n slack --patch-file k8s/ha/anti-affinity-patch.yaml

kubectl delete pod -n slack <web-pod>                  # app stays up
kubectl delete pod -n slack $(kubectl get cluster slack-pg -n slack -o jsonpath='{.status.currentPrimary}')
kubectl drain <node> --ignore-daemonsets --delete-emptydir-data --force ; kubectl uncordon <node>
```

## Helm basics

```bash
helm repo add <name> <url> && helm repo update
helm install <release> <repo>/<chart> -n <ns> --create-namespace
helm upgrade <release> <repo>/<chart> -n <ns> -f values.yaml
helm uninstall <release> -n <ns>
```

## "My pod won't start" quick triage
- `Pending` → no resources / unschedulable → `kubectl describe pod` events.
- `ImagePullBackOff` → forgot `kind load` or wrong tag/policy.
- `CrashLoopBackOff` → app erroring on boot → `kubectl logs`.
- `0/1 Ready` → failing readiness probe → check `/api/health/` + DB/Redis reachability.
