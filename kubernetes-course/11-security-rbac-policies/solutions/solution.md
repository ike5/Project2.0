# Challenge 11 — Reference Solution

### 1. Scoped writer
```bash
kubectl create namespace apps
kubectl create serviceaccount deployer -n apps
```
```yaml
# role + binding in namespace apps
apiVersion: rbac.authorization.k8s.io/v1
kind: Role
metadata: { name: deploy-manager, namespace: apps }
rules:
  - apiGroups: ["apps"]
    resources: ["deployments"]
    verbs: ["get","list","watch","create","update","patch","delete"]
---
apiVersion: rbac.authorization.k8s.io/v1
kind: RoleBinding
metadata: { name: deploy-manager, namespace: apps }
subjects:
  - kind: ServiceAccount
    name: deployer
    namespace: apps
roleRef: { kind: Role, name: deploy-manager, apiGroup: rbac.authorization.k8s.io }
```
```bash
SA=system:serviceaccount:apps:deployer
kubectl auth can-i create deployments -n apps    --as=$SA   # yes
kubectl auth can-i create deployments -n default --as=$SA   # no
kubectl auth can-i get    secrets     -n apps    --as=$SA   # no
```

### 2. Cluster-wide view
```bash
kubectl create serviceaccount viewer
kubectl create clusterrolebinding viewer-binding \
  --clusterrole=view --serviceaccount=default:viewer
SA=system:serviceaccount:default:viewer
kubectl auth can-i list   pods -A     --as=$SA   # yes
kubectl auth can-i delete pods        --as=$SA   # no
kubectl auth can-i get    secrets     --as=$SA   # no  (the built-in 'view' excludes secrets)
```

### 3. Harden a workload (see manifests/compliant-pod.yaml)
The key is a `securityContext` that satisfies `restricted`:
```yaml
spec:
  securityContext:
    runAsNonRoot: true
    seccompProfile: { type: RuntimeDefault }
  containers:
    - name: web-api
      image: web-api:1.0           # already non-root (USER appuser)
      imagePullPolicy: Never
      securityContext:
        allowPrivilegeEscalation: false
        runAsNonRoot: true
        capabilities: { drop: ["ALL"] }
```
> Plain `nginx:1.27` binds :80 as root and fails `restricted`. Use a non-root image
> (e.g. `nginxinc/nginx-unprivileged`) or our `web-api`.

### 4. Egress policy (Calico)
```yaml
apiVersion: networking.k8s.io/v1
kind: NetworkPolicy
metadata: { name: web-egress-dns-only, namespace: netpol-demo }
spec:
  podSelector: { matchLabels: { app: web } }
  policyTypes: ["Egress"]
  egress:
    - to:
        - namespaceSelector: {}
          podSelector:
            matchLabels:
              k8s-app: kube-dns
      ports:
        - { protocol: UDP, port: 53 }
        - { protocol: TCP, port: 53 }
```
```bash
# from a web pod: nslookup works, but wget to another pod/external times out
kubectl --context kind-netpol exec -n netpol-demo deploy/web -- nslookup kubernetes.default
```

### 5. Stretch — secrets risk
> A workload SA that can `get secrets` cluster-wide can read **every** credential in
> the cluster (DB passwords, tokens, TLS keys). If that Pod is compromised (RCE,
> SSRF), the attacker harvests all of them — total cluster compromise.
> **Mitigations:** (1) scope secret access with namespaced Roles to only the specific
> secrets a workload needs; (2) enable etcd **encryption at rest** and/or use an
> external secret manager (Vault, cloud KMS, External Secrets Operator) so secrets
> aren't broadly readable via the API at all.

Cleanup:
```bash
kubectl delete ns apps --ignore-not-found
kubectl delete clusterrolebinding viewer-binding --ignore-not-found
kubectl delete sa viewer --ignore-not-found
```
