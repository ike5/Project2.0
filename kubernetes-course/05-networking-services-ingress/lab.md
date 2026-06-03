# Lab 05 — Services, DNS & Ingress

**You'll:** front Pods with a Service, watch DNS-based load balancing, try a
NodePort, then install ingress-nginx and route two apps by path. ⏱️ ~55 min.

> Prereqs: cluster up; `web-api:1.0` loaded.

---

## Part A — Deploy + ClusterIP Service

```bash
cd 05-networking-services-ingress
kubectl apply -f manifests/deploy-and-service.yaml
kubectl get svc web
kubectl get endpoints web        # should list 3 Pod IPs (the Ready backends)
```
✅ The Service `web` has a stable ClusterIP and 3 endpoints. If endpoints are
empty, your selector doesn't match the Pod labels (see troubleshooting cheatsheet).

## Part B — DNS-based load balancing

```bash
kubectl run client --rm -it --image=busybox:1.36 --restart=Never -- sh
  # inside the cluster:
  nslookup web                                  # resolves to the Service ClusterIP
  for i in $(seq 6); do wget -qO- http://web/ ; echo; done
  exit
```
✅ `nslookup web` resolves by **name** (CoreDNS). The repeated `wget`s show
different `served_by` pod names — the Service is load-balancing across endpoints.

Test readiness affecting endpoints:
```bash
POD=$(kubectl get pod -l app=web -o jsonpath='{.items[0].metadata.name}')
kubectl port-forward "$POD" 8080:8080 &
curl -sX POST localhost:8080/toggle-ready >/dev/null    # make this pod not-ready
kill %1
sleep 8
kubectl get endpoints web      # now only 2 endpoints — the not-ready pod was removed
```
✅ Readiness gates traffic: the Service stopped routing to the not-ready Pod.

## Part C — NodePort

```bash
kubectl apply -f manifests/nodeport.yaml
kubectl get svc web-nodeport
# In kind, node IPs are internal; the easy way to reach a NodePort locally is via
# the control-plane container's mapped network. Simplest local check:
kubectl port-forward svc/web-nodeport 8080:80 &
curl -s localhost:8080/ ; echo
kill %1
```
> On a real cluster you'd hit `http://<any-node-ip>:30080`. On kind, port-forward or
> Ingress are the friendlier local options — which is exactly why we use Ingress next.

## Part D — Install the Ingress controller (ingress-nginx for kind)

```bash
kubectl apply -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml

# wait for the controller to be ready
kubectl wait --namespace ingress-nginx \
  --for=condition=Ready pod \
  --selector=app.kubernetes.io/component=controller \
  --timeout=120s
```
✅ A controller Pod runs in the `ingress-nginx` namespace. It binds host ports
80/443 (mapped from your Mac by the kind config in Module 00).

## Part E — Route two apps by path

```bash
kubectl apply -f manifests/second-app.yaml      # the "api" app + service
kubectl apply -f manifests/ingress.yaml
kubectl get ingress apps
```
Now hit it from your Mac's browser/curl (no port-forward needed!):
```bash
curl -s http://localhost/ ; echo            # COLOR blue   -> web service
curl -s http://localhost/api/ ; echo        # COLOR green  -> api service, greeting "Hello from the API service"
curl -s http://localhost/api/config ; echo  # routed to api, path rewritten to /config
```
✅ One entry point (`localhost:80`), routed to different Services by path. The
`rewrite-target` annotation strips `/api` so the backend sees `/` and `/config`.

## Part F — Inspect

```bash
kubectl describe ingress apps        # see the rules and the backends
kubectl logs -n ingress-nginx -l app.kubernetes.io/component=controller --tail=20
```

## Cleanup
```bash
kubectl delete -f manifests/
# (leave ingress-nginx installed; later modules can reuse it. To remove it:)
# kubectl delete -f https://raw.githubusercontent.com/kubernetes/ingress-nginx/main/deploy/static/provider/kind/deploy.yaml
```

## What you learned
- Services give stable identity + load balancing; endpoints follow readiness.
- CoreDNS lets Pods find Services by name (`svc.namespace.svc.cluster.local`).
- NodePort vs ClusterIP vs LoadBalancer; why Ingress is nicer for HTTP.
- Ingress routes by host/path through a controller you must install.

➡️ **[challenge.md](./challenge.md)** then [Module 06](../06-storage/).
