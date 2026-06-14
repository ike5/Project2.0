# Challenge 16 — Reference Solution

### 1. Error-rate alert
```yaml
groups:
  - name: slack-web
    rules:
      - alert: WebHighErrorRate
        expr: |
          sum(rate(django_http_responses_total_by_status_total{status=~"5.."}[5m]))
            / sum(rate(django_http_responses_total_by_status_total[5m])) > 0.05
        for: 5m
        labels: {severity: page}
        annotations: {summary: "web 5xx > 5% for 5m"}
```
> **Page** on user-facing symptoms (high error rate, full outage, p95 latency blown).
> **Ticket** on causes that aren't yet user-visible (a node down but capacity fine, a
> replica restarting). Page on symptoms, not every cause, to avoid alert fatigue.

### 2. Hardened securityContext
```yaml
securityContext:
  runAsNonRoot: true
  allowPrivilegeEscalation: false
  capabilities: {drop: ["ALL"]}
  readOnlyRootFilesystem: true
volumeMounts: [{name: tmp, mountPath: /tmp}]
volumes: [{name: tmp, emptyDir: {}}]   # writable /tmp since the root FS is read-only
```

### 3. Sealed Secrets
```bash
kubeseal --format yaml < k8s/base/secret.plain.yaml > k8s/base/backend-sealedsecret.yaml
# commit ONLY the SealedSecret; the controller decrypts it into a real Secret in-cluster
kubectl apply -f k8s/base/backend-sealedsecret.yaml
```
> Git holds only ciphertext; the private key never leaves the cluster.

### 4. Quota + LimitRange
```yaml
apiVersion: v1
kind: ResourceQuota
metadata: {name: slack-quota, namespace: slack}
spec: {hard: {requests.cpu: "4", requests.memory: 8Gi, limits.cpu: "8", limits.memory: 16Gi}}
---
apiVersion: v1
kind: LimitRange
metadata: {name: slack-defaults, namespace: slack}
spec:
  limits:
    - type: Container
      default: {cpu: 300m, memory: 256Mi}
      defaultRequest: {cpu: 100m, memory: 128Mi}
```
A pod with no requests inherits the defaults; one that pushes the namespace over quota
is rejected at admission.

### 5. CI/CD pipeline (sketch)
```
CI:  ruff && pytest            # backend
     tsc --noEmit && next build # frontend
     docker build + trivy scan  # fail on HIGH/CRITICAL
     push images by @sha256 digest
CD:  kubectl apply migrate Job; wait --for=complete
     argocd app sync / kubectl set image (by digest)
     kubectl rollout status --timeout=300s || kubectl rollout undo
```
> The single biggest safeguard is **readiness-gated rollout with automatic rollback**:
> `maxUnavailable: 0` plus a health-checked `rollout status` means a broken image never
> takes over from healthy pods — it fails its probe, the rollout stalls, and `undo`
> restores the last good version before users notice.
