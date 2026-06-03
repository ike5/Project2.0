# Challenge 10 — Reference Solution

### 1. Optional Ingress in the chart
Add to `values.yaml`:
```yaml
ingress:
  enabled: false
  host: web.localdev.me
```
Create `templates/ingress.yaml`:
```yaml
{{- if .Values.ingress.enabled }}
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: {{ include "web-api.fullname" . }}
  labels:
    {{- include "web-api.labels" . | nindent 4 }}
spec:
  ingressClassName: nginx
  rules:
    - host: {{ .Values.ingress.host | quote }}
      http:
        paths:
          - path: /
            pathType: Prefix
            backend:
              service:
                name: {{ include "web-api.fullname" . }}
                port:
                  number: {{ .Values.service.port }}
{{- end }}
```
```bash
helm template web ./web-api | grep -c "kind: Ingress"          # 0
helm template web ./web-api --set ingress.enabled=true | grep -c "kind: Ingress"   # 1
```

### 2. values-dev.yaml
```yaml
replicaCount: 1
config:
  greeting: "Hello from DEV (debug)"
  color: "lime"
```
```bash
diff <(helm template web ./web-api -f values-dev.yaml) \
     <(helm template web ./web-api -f values-prod.yaml)   # differs in replicas + env values only
```

### 3. staging overlay
`overlays/staging/kustomization.yaml`:
```yaml
apiVersion: kustomize.config.k8s.io/v1beta1
kind: Kustomization
namePrefix: stg-
resources: [ ../../base ]
replicas:
  - { name: web-api, count: 2 }
labels:
  - pairs: { env: staging }
    includeSelectors: false
patches:
  - target: { kind: Deployment, name: web-api }
    patch: |
      - op: replace
        path: /spec/template/spec/containers/0/env/0/value
        value: "amber"
```
```bash
kubectl kustomize overlays/staging | grep -E 'name:|replicas:|env:|value:|env:'
```

### 4. configMapGenerator
In `base/kustomization.yaml`:
```yaml
configMapGenerator:
  - name: web-config
    literals:
      - LOG_LEVEL=info
      - FEATURE_X=true
```
Wire into `base/deployment.yaml`:
```yaml
          envFrom:
            - configMapRef:
                name: web-config
```
```bash
kubectl kustomize overlays/dev | grep -A1 "kind: ConfigMap"   # name is web-config-<hash>
```
> **Why the hash matters:** Kustomize appends a content hash to generated
> ConfigMap/Secret names and rewrites references. Change the data → new hash → new
> object name → the Deployment's pod template changes → **a rollout is triggered
> automatically**. This solves the "ConfigMap changed but Pods didn't restart"
> problem from Module 04.

### 5. Stretch — when each wins
> **Helm wins** when packaging software for *others* to install with many tunables
> and you need versioned releases + `helm rollback` (e.g. publishing a database
> operator chart). **Kustomize wins** when you own the manifests and just need a few
> environment variants of the same app — plain YAML, no templating language, native
> to `kubectl`, and generator hashes give free rollout-on-config-change.
