# Module 10 — Packaging: Helm & Kustomize

**Goal:** stop copy-pasting near-identical YAML for dev/staging/prod. Template and
manage applications with **Helm** and **Kustomize**, and know when to use which.

⏱️ ~2.5 hours · 🎯 Prereq: Modules 00–09. `helm` installed; `web-api:1.0` loaded.

---

## 1. The problem

You have a Deployment + Service + ConfigMap. Now you need them in `dev` (1 replica,
debug logging) and `prod` (5 replicas, real config). Maintaining two full copies of
the YAML means drift and mistakes. Two tools solve this differently.

## 2. Helm — the package manager (templating)

**Helm** packages a set of manifests into a **chart**. Manifests become Go
**templates** with values injected from `values.yaml`. You install a chart as a
named **release**; Helm tracks revisions so you can upgrade and roll back.

```
mychart/
├── Chart.yaml          # name, version, description
├── values.yaml         # default values
└── templates/
    ├── deployment.yaml # uses {{ .Values.replicaCount }}, etc.
    ├── service.yaml
    └── _helpers.tpl    # reusable template snippets
```

Core commands:
```bash
helm install web ./web-api                      # install a release named "web"
helm install web ./web-api -f values-prod.yaml  # override values for prod
helm install web ./web-api --set replicaCount=5 # override one value
helm upgrade web ./web-api --set image.tag=2.0  # ship a change
helm rollback web 1                             # revert to revision 1
helm list                                        # releases
helm uninstall web                               # remove
helm template web ./web-api                      # render to YAML WITHOUT installing (great for review)
```

**Strengths:** parameterization, versioned releases, rollbacks, a huge ecosystem of
public charts (you already used one: kube-prometheus-stack). **Trade-off:** Go
templating in YAML can get gnarly.

## 3. Kustomize — template-free overlays

**Kustomize** (built into `kubectl` as `kubectl apply -k`) takes plain YAML (a
**base**) and applies **overlays** that *patch* it per environment — no templating
language. You only express the *differences*.

```
kustomize/
├── base/
│   ├── kustomization.yaml   # lists the base resources + common labels
│   ├── deployment.yaml      # plain, valid YAML
│   └── service.yaml
└── overlays/
    ├── dev/kustomization.yaml    # patches: 1 replica, dev name prefix
    └── prod/kustomization.yaml   # patches: 5 replicas, prod settings
```

Core commands:
```bash
kubectl kustomize overlays/dev          # render dev to stdout (review)
kubectl apply -k overlays/dev           # build + apply dev
kubectl apply -k overlays/prod          # build + apply prod
kubectl delete -k overlays/dev
```

Overlays can change replicas, images (`images:` field), add a `namePrefix`/`suffix`,
inject `commonLabels`, generate ConfigMaps/Secrets (`configMapGenerator`), and patch
any field via strategic-merge or JSON patches.

**Strengths:** no new language, plain YAML stays valid, great for env variants.
**Trade-off:** less powerful for complex conditional logic and no built-in
release/rollback tracking.

## 4. Which should I use?

| Use **Helm** when… | Use **Kustomize** when… |
|--------------------|--------------------------|
| Distributing an app for others to install/configure | Managing *your own* app across a few environments |
| You need release history + `helm rollback` | You want plain YAML with no templating |
| Installing third-party software (Prometheus, Argo CD) | You want `kubectl`-native, zero extra tooling |

They're not mutually exclusive — many teams template with Helm *and* post-process
with Kustomize. For your own apps, Kustomize is often the simpler start.

---

## Do the lab
Convert `web-api` into a Helm chart (install, override, upgrade, rollback), then do
the same with a Kustomize base + dev/prod overlays. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Provided artifacts
- Helm chart: [`manifests/helm/web-api/`](./manifests/helm/web-api/)
- Kustomize: [`manifests/kustomize/`](./manifests/kustomize/) (base + overlays/dev + overlays/prod)

## Key terms
chart · release · revision · values · `helm upgrade/rollback` · `helm template` ·
Kustomize · base · overlay · patch · `namePrefix` · `kubectl apply -k`

**Next →** [Module 11: Security — RBAC & Policies](../11-security-rbac-policies/)
