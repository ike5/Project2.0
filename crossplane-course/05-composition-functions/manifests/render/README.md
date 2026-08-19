# Offline rendering

These three files are everything `crossplane render` needs. No cluster, no
provider, no AWS.

```bash
cd 05-composition-functions/manifests/render
crossplane render xr.yaml ../composition-templated.yaml functions.yaml
```

Change `zones` in `xr.yaml`, re-run, and see the output change immediately.

Useful variations:

```bash
# Include what the XR's own status would look like
crossplane render xr.yaml ../composition-templated.yaml functions.yaml --include-full-xr

# Count what gets produced
crossplane render xr.yaml ../composition-templated.yaml functions.yaml \
  | grep -c '^kind:'

# Diff two inputs to see exactly what a spec change does
crossplane render xr.yaml ../composition-templated.yaml functions.yaml > /tmp/a.yaml
# ...edit xr.yaml...
crossplane render xr.yaml ../composition-templated.yaml functions.yaml > /tmp/b.yaml
diff /tmp/a.yaml /tmp/b.yaml
```

That last one is the closest thing Crossplane has to `terraform plan` for
composition changes, and it is genuinely useful in code review.

**Requires Docker running**, since the functions execute as local containers.
