# acme-platform

The complete platform from Modules 07–09, packaged.

## Build and push

```bash
cd solutions/platform-package
crossplane xpkg build --package-root=. --package-file=acme-platform.xpkg
crossplane xpkg push --package-files=acme-platform.xpkg ghcr.io/acme/platform:v1.0.0
```

## Clean-cluster test (this is the real success criterion)

```bash
00-setup/scripts/delete-cluster.sh && 00-setup/scripts/create-cluster.sh
00-setup/scripts/install-crossplane.sh
00-setup/scripts/install-aws-emulator.sh

kubectl apply -f - <<'YAML'
apiVersion: pkg.crossplane.io/v1
kind: Configuration
metadata:
  name: acme-platform
spec:
  package: ghcr.io/acme/platform:v1.0.0
YAML

kubectl get configurations,providers,functions -w
```

Four providers and four functions install themselves. You installed none of them.

## What this package deliberately does NOT contain

1. **ProviderConfigs** — they carry credentials and an endpoint specific to one
   installation.
2. **EnvironmentConfigs** — they carry *your* account IDs and OIDC hosts.

Both must come from the consumer. That separation is the point: the package is the
same artifact everywhere, and the facts differ per installation.

## Populate the XRDs and Compositions

To make this buildable, copy the module manifests in:

```bash
cp ../../../07-aws-networking/manifests/xrd.yaml            apis/xnetwork.yaml
cp ../../../08-aws-iam-and-identity/manifests/xrd.yaml      apis/xappidentity.yaml
cp ../../../09-aws-data-services/manifests/xrd.yaml         apis/xdatabase.yaml
cp ../../../07-aws-networking/manifests/composition.yaml    compositions/xnetwork-aws.yaml
cp ../../manifests/composition-envconfig.yaml               compositions/xappidentity-aws.yaml
cp ../../../09-aws-data-services/manifests/composition.yaml compositions/xdatabase-aws.yaml
```

They're referenced rather than duplicated so there is one source of truth — a
duplicated composition is a composition that will drift.
