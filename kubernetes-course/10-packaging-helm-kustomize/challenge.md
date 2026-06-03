# Challenge 10 — Template Like a Pro

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Extend the Helm chart.** Add a templated, *optional* Ingress to the chart:
   `ingress.enabled` (default false), `ingress.host`. When enabled, `helm template`
   should render an Ingress; when disabled, none. (Hint: `{{- if .Values.ingress.enabled }}`.)

2. **Per-env Helm.** Create `values-dev.yaml` (1 replica, debug greeting) and prove
   `helm template web ./web-api -f values-dev.yaml` differs from prod only where intended.

3. **Add a Kustomize overlay.** Create a `staging` overlay: 2 replicas, `namePrefix:
   stg-`, COLOR `amber`, and a `commonLabels: { env: staging }`. Render it and verify.

4. **ConfigMap generator.** Use Kustomize's `configMapGenerator` in the base to
   create a ConfigMap from literals, wire it into the Deployment via `envFrom`, and
   observe the hashed ConfigMap name (and why that hash matters for rollouts).

5. **Stretch:** Explain, in 2–3 sentences, a scenario where Helm's templating is
   clearly better than Kustomize, and one where Kustomize is clearly better.

## Success criteria
- [ ] Chart conditionally renders an Ingress based on a value.
- [ ] `values-dev.yaml` produces the intended dev-only differences.
- [ ] A working `staging` overlay with the required changes.
- [ ] `configMapGenerator` produces a hash-suffixed ConfigMap consumed by the Deployment.
- [ ] Clear articulation of Helm-vs-Kustomize trade-offs.
