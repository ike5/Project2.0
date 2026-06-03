# Lab 11 — RBAC, Pod Security & NetworkPolicies

**You'll:** build a least-privilege ServiceAccount and test it, enforce `restricted`
Pod Security, and (optionally) prove NetworkPolicy enforcement on Calico. ⏱️ ~75 min.

> Prereqs: cluster up; `web-api:1.0` loaded.

---

## Part A — RBAC + ServiceAccount (least privilege)

```bash
cd 11-security-rbac-policies
kubectl apply -f manifests/serviceaccount.yaml
kubectl apply -f manifests/role.yaml
kubectl apply -f manifests/rolebinding.yaml
```

Test exactly what this identity can and cannot do with `auth can-i`:
```bash
SA=system:serviceaccount:default:pod-reader
kubectl auth can-i list   pods       --as=$SA      # yes
kubectl auth can-i get    pods       --as=$SA      # yes
kubectl auth can-i delete pods       --as=$SA      # no
kubectl auth can-i list   secrets    --as=$SA      # no
kubectl auth can-i list   pods -n kube-system --as=$SA   # no (Role is namespaced to default)
```
✅ The SA can only read Pods in `default` — nothing more. That's least privilege.

### See it from inside a Pod
Run a Pod *as* the SA and call the API with its mounted token:
```bash
kubectl run reader --image=bitnami/kubectl:latest --restart=Never \
  --overrides='{"spec":{"serviceAccountName":"pod-reader"}}' \
  --command -- sleep 3600
kubectl exec reader -- kubectl get pods                 # works (allowed)
kubectl exec reader -- kubectl get secrets 2>&1 | tail -1   # Forbidden
kubectl delete pod reader
```
✅ The app authenticated automatically with its SA token and was correctly limited.

## Part B — Pod Security Standards

```bash
kubectl apply -f manifests/restricted-ns.yaml
# try to run a root nginx -> REJECTED at admission:
kubectl apply -f manifests/violating-pod.yaml
```
✅ Expected error (not just a warning — the create is blocked):
```
Error from server (Forbidden): ... violates PodSecurity "restricted:latest":
allowPrivilegeEscalation != false, unrestricted capabilities, runAsNonRoot != true, seccompProfile ...
```
Now the compliant Pod is admitted:
```bash
kubectl apply -f manifests/compliant-pod.yaml
kubectl get pod good -n secure          # Running
```
✅ Same namespace, same admission controller — hardening makes the difference.

Cleanup:
```bash
kubectl delete -f manifests/compliant-pod.yaml --ignore-not-found
kubectl delete ns secure
```

## Part C — NetworkPolicies (default-deny + narrow allow)

Apply the test apps on your normal cluster first:
```bash
kubectl apply -f manifests/netpol-test-apps.yaml
kubectl wait -n netpol-demo --for=condition=Available deployment/web --timeout=60s
```
Baseline — everything can reach `web` (no policy yet):
```bash
kubectl run probe -n netpol-demo --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- --timeout=3 http://web/ ; echo
```
✅ Works (you get a JSON response).

Now apply default-deny + the narrow allow:
```bash
kubectl apply -f manifests/netpol-deny-all.yaml
kubectl apply -f manifests/netpol-allow-from-client.yaml
```

> ⚠️ **On the default kind cluster (kindnet), these policies are NOT enforced** — the
> probe below will still succeed even though it "should" be denied. That is the
> lesson: *NetworkPolicy objects are inert without an enforcing CNI.* To see real
> enforcement, do Part D on a Calico cluster.

Test from a DISALLOWED client (no `access=web-client` label):
```bash
kubectl run probe -n netpol-demo --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- --timeout=3 http://web/ ; echo
# kindnet: succeeds (not enforced). Calico: times out (denied).
```
Test from an ALLOWED client (labeled correctly):
```bash
kubectl run probe -n netpol-demo --rm -it --image=busybox:1.36 --restart=Never \
  --labels=access=web-client -- \
  wget -qO- --timeout=3 http://web/ ; echo
# Calico: succeeds (allowed by the policy).
```

## Part D — (Optional) Real enforcement with Calico

Spin up a dedicated cluster whose CNI enforces policies:
```bash
kind create cluster --name netpol --config manifests/kind-calico.yaml
kubectl --context kind-netpol apply -f https://raw.githubusercontent.com/projectcalico/calico/v3.28.0/manifests/calico.yaml
kubectl --context kind-netpol -n kube-system rollout status ds/calico-node --timeout=180s

# load the image into THIS cluster and redo Part C against it:
kind load docker-image web-api:1.0 --name netpol
kubectl --context kind-netpol apply -f manifests/netpol-test-apps.yaml
kubectl --context kind-netpol wait -n netpol-demo --for=condition=Available deployment/web --timeout=90s
kubectl --context kind-netpol apply -f manifests/netpol-deny-all.yaml
kubectl --context kind-netpol apply -f manifests/netpol-allow-from-client.yaml

# disallowed client -> TIMES OUT now:
kubectl --context kind-netpol run probe -n netpol-demo --rm -it --image=busybox:1.36 --restart=Never -- \
  wget -qO- --timeout=3 http://web/ ; echo
# allowed client -> SUCCEEDS:
kubectl --context kind-netpol run probe -n netpol-demo --rm -it --image=busybox:1.36 --restart=Never \
  --labels=access=web-client -- wget -qO- --timeout=3 http://web/ ; echo
```
✅ On Calico the default-deny truly blocks the unlabeled client while the labeled
client is allowed. Tear down when done:
```bash
kind delete cluster --name netpol
```

## Cleanup (normal cluster)
```bash
kubectl delete -f manifests/netpol-allow-from-client.yaml -f manifests/netpol-deny-all.yaml -f manifests/netpol-test-apps.yaml --ignore-not-found
kubectl delete -f manifests/rolebinding.yaml -f manifests/role.yaml -f manifests/serviceaccount.yaml --ignore-not-found
```

## What you learned
- RBAC: Roles/Bindings grant least-privilege; `auth can-i` and SA tokens prove it.
- Pod Security admission *rejects* non-compliant Pods by namespace label.
- NetworkPolicies are default-deny + allow — **but only if your CNI enforces them**.

➡️ **[challenge.md](./challenge.md)** then [Module 12](../12-production-and-gitops/).
