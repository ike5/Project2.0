# Installing Argo CD on the course cluster

```bash
kubectl create namespace argocd
kubectl apply -n argocd \
  -f https://raw.githubusercontent.com/argoproj/argo-cd/v2.13.2/manifests/install.yaml
kubectl wait --for=condition=Available deploy --all -n argocd --timeout=10m
```

Get the admin password and open the UI:
```bash
kubectl -n argocd get secret argocd-initial-admin-secret \
  -o jsonpath='{.data.password}' | base64 -d; echo
kubectl port-forward svc/argocd-server -n argocd 8080:443
# https://localhost:8080  (user: admin — accept the self-signed certificate)
```

> On a kind cluster Argo CD is a heavy addition. If your laptop struggles, run this
> module's Parts A–E and skip the UI: everything is verifiable with `kubectl`.
