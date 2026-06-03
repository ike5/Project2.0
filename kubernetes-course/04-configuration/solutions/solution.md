# Challenge 04 — Reference Solution

### 1. File-mounted config
```yaml
# pod-files.yaml
apiVersion: v1
kind: Pod
metadata: { name: cfg-files }
spec:
  containers:
    - name: web-api
      image: web-api:1.0
      imagePullPolicy: Never
      volumeMounts:
        - name: cfg
          mountPath: /etc/web
  volumes:
    - name: cfg
      configMap:
        name: web-config
```
```bash
kubectl apply -f manifests/configmap.yaml      # ensure it exists
kubectl apply -f pod-files.yaml
kubectl exec cfg-files -- ls /etc/web           # COLOR  GREETING  APP_VERSION
kubectl exec cfg-files -- cat /etc/web/COLOR ; echo
```

### 2. Right-sized with startupProbe
```yaml
startupProbe:
  httpGet: { path: /healthz, port: 8080 }
  failureThreshold: 30      # up to 30 * periodSeconds for slow boot
  periodSeconds: 2
livenessProbe:
  httpGet: { path: /healthz, port: 8080 }
  periodSeconds: 10
readinessProbe:
  httpGet: { path: /readyz, port: 8080 }
  periodSeconds: 5
resources:
  requests: { cpu: "100m", memory: "64Mi" }
  limits:   { cpu: "300m", memory: "128Mi" }
```
> With a startupProbe, liveness/readiness don't run until startup succeeds, so a
> slow boot can't trigger a restart loop.

### 3. Fix the CrashLoop
```bash
kubectl apply -f solutions/bad-liveness.yaml
kubectl get pod bad-liveness -w        # CrashLoopBackOff / RESTARTS climbing
kubectl describe pod bad-liveness | grep -A3 Liveness
#   Liveness probe failed: HTTP probe failed with statuscode: 404
```
Fix: point the probe at the real health endpoint and give it breathing room:
```yaml
livenessProbe:
  httpGet: { path: /healthz, port: 8080 }   # was /nope
  initialDelaySeconds: 5                     # was 0
  periodSeconds: 10
  failureThreshold: 3                        # was 1
```
```bash
kubectl delete pod bad-liveness
# (re-apply the corrected manifest) -> stays Running, RESTARTS stops climbing
```

### 4. Roll out a Secret change
```bash
kubectl patch secret web-secret -p '{"stringData":{"API_TOKEN":"rotated-token"}}'
# env-injected secrets are read at container start, so:
kubectl rollout restart deployment/web
```
> A plain `apply` updates the Secret object, but Pods that consumed it as **env
> vars** only read it at startup — they won't see the new value until restarted.
> (Secrets mounted as **files** do update in-place over time, but the app must
> re-read the file.)

Cleanup: `kubectl delete pod cfg-files bad-liveness --ignore-not-found`
