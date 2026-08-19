# acme-platform — a Crossplane Configuration package

A complete, buildable example of shipping a platform API as a versioned artifact.

## Layout

```
package/
├── crossplane.yaml       ← metadata + dependencies (required, at the root)
├── apis/                 ← XRDs
│   └── xbucket.yaml
└── compositions/         ← Compositions
    └── xbucket-aws.yaml
```

Directory names are conventional, not required — `xpkg build` bundles every YAML
under the package root. Keeping APIs and implementations separate makes review
easier, because a change under `apis/` is a change to your public contract.

## Build

```bash
cd manifests/package
crossplane xpkg build --package-root=. --package-file=acme-platform.xpkg
```
The result is an OCI image tarball. Inspect it like any container image.

## Push

```bash
crossplane xpkg push \
  --package-files=acme-platform.xpkg \
  ghcr.io/acme/platform:v1.0.0
```

Any OCI registry works — GHCR, ECR, Artifactory, Harbor — so your existing
mirroring, scanning, and access control apply unchanged.

## Install (what a consumer does)

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Configuration
metadata:
  name: acme-platform
spec:
  package: ghcr.io/acme/platform:v1.0.0
```

That single object installs the XRDs, the Compositions, **and** the two providers
and three functions declared in `dependsOn`. The consumer needs to know none of it.

## Versioning rules

| Change | Bump | Notes |
|--------|------|-------|
| New optional field with a default | minor | Safe |
| New Composition | minor | Safe |
| Changed field semantics | **major** | Existing XRs change behaviour |
| Removed field | **major** | Breaks consumers |
| **Renamed a resource in a composition** | **major** | **Deletes and recreates infrastructure** |

That last row is the one that catches people: it's invisible in the API surface and
destructive to every existing XR. Resource name annotations are part of your public
contract.

**Never publish `:latest`.** A consumer pinned to it gets your next commit applied to
their production infrastructure at a moment they did not choose.
