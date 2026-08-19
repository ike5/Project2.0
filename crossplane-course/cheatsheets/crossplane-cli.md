# Crossplane CLI & kubectl Cheatsheet

Crossplane has **no daily-driver CLI**. You operate it with `kubectl`, exactly like
any other Kubernetes API. The `crossplane` binary is for *authoring* — rendering,
validating, and packaging.

---

## The commands you'll actually type all day

```bash
# What did my XR create, and is any of it broken?
crossplane trace <kind> <name> [-n <namespace>]

# Everything Crossplane manages, everywhere
kubectl get managed                      # every managed resource, all providers
kubectl get composite                    # every XR
kubectl get providers,functions          # installed packages

# The two columns that matter
kubectl get managed
# NAME      SYNCED   READY   EXTERNAL-NAME   AGE
#   SYNCED = did the API call succeed?
#   READY  = does the resource actually exist and work?
```

## Reading state

```bash
kubectl get bucket my-bucket -o yaml               # full object
kubectl describe bucket my-bucket                  # Events at the bottom — read these
kubectl get bucket my-bucket -o jsonpath='{.status.conditions}' | jq

# The real cloud identity of a resource
kubectl get bucket my-bucket \
  -o jsonpath='{.metadata.annotations.crossplane\.io/external-name}'

# Why is my XR not ready? (conditions of everything it owns)
crossplane trace xdatabase my-db -n team-a -o wide
```

## Logs — where to look when nothing else helps

```bash
# The composition engine: XRD/Composition/XR problems
kubectl logs -n crossplane-system deploy/crossplane -f

# A provider: cloud API problems (auth, quota, invalid params)
kubectl logs -n crossplane-system -l pkg.crossplane.io/provider=provider-aws-s3 -f

# A function: rendering problems
kubectl logs -n crossplane-system -l pkg.crossplane.io/function=function-go-templating -f
```

## Authoring: test compositions with no cluster

This is the fastest feedback loop in Crossplane. Use it constantly.

```bash
# Render an XR through a composition + functions, print what would be created
crossplane render xr.yaml composition.yaml functions.yaml

# Include what the XR's status would look like
crossplane render xr.yaml composition.yaml functions.yaml --include-full-xr

# Feed in EnvironmentConfigs or other cluster context
crossplane render xr.yaml composition.yaml functions.yaml \
  --extra-resources=extra.yaml

# Validate the rendered output against real schemas
crossplane render xr.yaml composition.yaml functions.yaml \
  | crossplane validate xrd.yaml -
```

`functions.yaml` is a plain list of `Function` objects annotated with where to get
the runtime:

```yaml
apiVersion: pkg.crossplane.io/v1
kind: Function
metadata:
  name: function-patch-and-transform
  annotations:
    render.crossplane.io/runtime: Development   # or Docker (the default)
spec:
  package: xpkg.upbound.io/crossplane-contrib/function-patch-and-transform:v0.8.2
```

## Packaging

```bash
crossplane xpkg build --package-root=. --package-file=platform.xpkg
crossplane xpkg push  --package-files=platform.xpkg xpkg.example.io/team/platform:v1.0.0
crossplane xpkg install configuration xpkg.example.io/team/platform:v1.0.0
```

## Emergency brakes

```bash
# Stop reconciling ONE resource (it stays, Crossplane stops touching it)
kubectl annotate bucket my-bucket crossplane.io/paused=true
kubectl annotate bucket my-bucket crossplane.io/paused-      # resume

# Delete the Kubernetes object but LEAVE the cloud resource alive
kubectl patch bucket my-bucket --type=merge \
  -p '{"spec":{"deletionPolicy":"Orphan"}}'
kubectl delete bucket my-bucket

# Pin an XR to its current composition revision before you change the composition
kubectl patch xdatabase my-db -n team-a --type=merge \
  -p '{"spec":{"crossplane":{"compositionUpdatePolicy":"Manual"}}}'
```

> **Stuck deleting?** Almost always a finalizer waiting on a cloud API that's
> refusing (a bucket with objects in it, a VPC with subnets). Fix the real cause
> first. Removing a finalizer by hand orphans the cloud resource silently — it is
> a last resort, not a fix:
> ```bash
> kubectl patch bucket my-bucket --type=merge -p '{"metadata":{"finalizers":[]}}'
> ```

## Package management

```bash
kubectl get providers
kubectl get functions
kubectl get configurations
kubectl get providerrevisions              # every version ever installed

# Upgrade a provider: just change the tag
kubectl patch provider provider-aws-s3 --type=merge \
  -p '{"spec":{"package":"xpkg.upbound.io/upbound/provider-aws-s3:v1.22.0"}}'
```

## Verifying against "AWS" itself

Don't trust Crossplane's status alone — ask AWS. Keep this alias handy:

```bash
awslocal() {
  kubectl run awscli-$RANDOM --rm -i --restart=Never -q \
    --image=amazon/aws-cli:2.18.9 \
    --env=AWS_ACCESS_KEY_ID=test \
    --env=AWS_SECRET_ACCESS_KEY=test \
    --env=AWS_DEFAULT_REGION=us-east-1 \
    -- --endpoint-url=http://moto.aws-local.svc.cluster.local:5000 "$@"
}

awslocal s3 ls
awslocal ec2 describe-vpcs
awslocal rds describe-db-instances
awslocal iam list-roles
```

## Useful jq/jsonpath one-liners

```bash
# Everything that is NOT synced
kubectl get managed -o json \
  | jq -r '.items[] | select(.status.conditions[]?|select(.type=="Synced" and .status!="True")) | .kind+"/"+.metadata.name'

# The message explaining a failure
kubectl get bucket my-bucket -o jsonpath='{.status.conditions[?(@.type=="Synced")].message}'

# Every resource an XR owns
kubectl get xdatabase my-db -n team-a -o jsonpath='{.spec.crossplane.resourceRefs[*].name}'
```
