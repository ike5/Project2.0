# Lab 04 — Config, Secrets, Resources & Probes

**You'll:** inject config via ConfigMap + Secret, prove env-vs-file behavior, set
resource limits, watch readiness pull a Pod from rotation, and trigger an OOMKill.
⏱️ ~55 min.

> Prereqs: cluster up; `web-api:1.0` loaded.

---

## Part A — Create the ConfigMap and Secret

```bash
cd 04-configuration
kubectl apply -f manifests/configmap.yaml
kubectl apply -f manifests/secret.yaml

kubectl get configmap web-config -o yaml
kubectl get secret web-secret -o yaml      # value is base64, NOT encrypted
echo "c3VwZXItc2VjcmV0LWRlbW8tdG9rZW4=" | base64 -d ; echo   # decode it yourself!
```
✅ You just decoded a Secret with no special privileges — internalize that Secrets
aren't encrypted by default.

You can also create them imperatively (handy):
```bash
kubectl create configmap demo --from-literal=FOO=bar --dry-run=client -o yaml
kubectl create secret generic demo --from-literal=PASS=hunter2 --dry-run=client -o yaml
```

## Part B — Deploy with config + Secret + probes + resources

```bash
kubectl apply -f manifests/web-deploy.yaml
kubectl rollout status deployment/web
kubectl get pods -l app=web
```
Confirm the config landed:
```bash
POD=$(kubectl get pod -l app=web -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$POD" -- printenv GREETING COLOR APP_VERSION
kubectl port-forward "$POD" 8080:8080 &
curl -s localhost:8080/config ; echo     # greeting from ConfigMap, api_token_present:true
kill %1
```
✅ `api_token_present` is `true` and the token is masked — the Secret was injected
without us hard-coding it.

## Part C — Env vars don't hot-reload (a key gotcha)

```bash
# change the ConfigMap
kubectl patch configmap web-config --type merge -p '{"data":{"COLOR":"magenta"}}'
kubectl exec "$POD" -- printenv COLOR        # STILL teal — env is read once at start

# to pick up the change, restart the pods:
kubectl rollout restart deployment/web
kubectl rollout status deployment/web
NEWPOD=$(kubectl get pod -l app=web -o jsonpath='{.items[0].metadata.name}')
kubectl exec "$NEWPOD" -- printenv COLOR      # now magenta
```
✅ **Lesson:** changing a ConfigMap does not update running Pods' env vars — restart them.

## Part D — Watch readiness probes work

`web-api` lets us toggle readiness at runtime. Watch a Pod leave/return to the
Service's endpoint set:
```bash
kubectl get endpoints web 2>/dev/null || echo "(no service yet — that's fine)"
# port-forward to one pod and flip it to not-ready:
kubectl port-forward "$NEWPOD" 8080:8080 &
curl -s localhost:8080/readyz ; echo          # {"status":"ready"}
curl -sX POST localhost:8080/toggle-ready ; echo   # now not-ready
sleep 8
kubectl get pod "$NEWPOD"                       # READY column shows 0/1 now
kubectl describe pod "$NEWPOD" | grep -A2 Readiness   # "Readiness probe failed: ... 503"
curl -sX POST localhost:8080/toggle-ready ; echo   # back to ready
sleep 8
kubectl get pod "$NEWPOD"                       # 1/1 again
kill %1
```
✅ A failing **readiness** probe makes the Pod `0/1` (not Ready) but does **not**
restart it. In Module 05 you'll see a Service automatically stop sending it traffic.

## Part E — Liveness probe restarts a container

Liveness failures *restart* the container. Our `/healthz` always returns 200, so to
see a restart, give the OOM demo a look instead, or simulate by killing the process:
```bash
kubectl exec "$NEWPOD" -- sh -c 'kill 1' 2>/dev/null || true
sleep 5
kubectl get pod "$NEWPOD"     # RESTARTS column increments; kubelet restarted the container
```

## Part F — OOMKilled

```bash
kubectl apply -f manifests/oom-demo.yaml
kubectl get pod oom-demo -w        # watch it go to OOMKilled / Error. Ctrl+C
kubectl describe pod oom-demo | grep -A3 "Last State"   # Reason: OOMKilled
kubectl logs oom-demo               # printed "allocated N MiB" until killed
```
✅ The container exceeded its 64Mi memory **limit** and the kernel killed it.

## Cleanup
```bash
kubectl delete -f manifests/
```

## What you learned
- Inject config/secrets via env or files; **env doesn't hot-reload** (restart to apply).
- Secrets are base64, not encrypted.
- requests drive scheduling; memory limits cause OOMKill, CPU limits cause throttling.
- readiness removes a Pod from traffic; liveness restarts it; startup protects slow boots.

➡️ **[challenge.md](./challenge.md)** then [Module 05](../05-networking-services-ingress/).
