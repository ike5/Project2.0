# Challenge 05 — Reference Solution

### 1. Diagnose a dead Service
```bash
kubectl apply -f solutions/broken-service.yaml
kubectl get endpoints web-broken           # <none> — the giveaway
kubectl get pods --show-labels             # pods are app=web
kubectl get svc web-broken -o jsonpath='{.spec.selector}{"\n"}'   # app=webapp — mismatch!
```
Fix the selector:
```bash
kubectl patch svc web-broken -p '{"spec":{"selector":{"app":"web"}}}'
kubectl get endpoints web-broken           # now 2 endpoints
```

### 2. Cross-namespace discovery
```bash
kubectl create ns team-a
kubectl apply -n team-a -f manifests/deploy-and-service.yaml
kubectl run client --rm -it --image=busybox:1.36 --restart=Never -- sh
  # from default namespace, must use the FQDN:
  wget -qO- http://web.team-a.svc.cluster.local/ ; echo
  exit
```
> **FQDN:** `web.team-a.svc.cluster.local` — `<service>.<namespace>.svc.cluster.local`.
> Within `team-a` you could just say `web`; across namespaces you need the FQDN.

Cleanup: `kubectl delete ns team-a`

### 3. Host-based Ingress
```yaml
# host-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: web-host
spec:
  ingressClassName: nginx
  rules:
    - host: web.localdev.me     # resolves to 127.0.0.1
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: web
                port: { number: 80 }
```
```bash
kubectl apply -f manifests/deploy-and-service.yaml   # ensure web exists
kubectl apply -f host-ingress.yaml
curl -s -H 'Host: web.localdev.me' http://localhost/ ; echo
# or directly: curl -s http://web.localdev.me/ ; echo
```

### 4. port vs targetPort
> - **`port`** = the port the *Service* listens on (what clients call, e.g. 80).
> - **`targetPort`** = the *container's* port the Service forwards to (e.g. 8080).
>
> If `targetPort` doesn't match the port the app actually listens on, the Service
> has endpoints but every connection is refused/times out — a classic "Service exists,
> endpoints exist, but nothing responds" bug.
