# Challenge 11 — Lock It Down

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Scoped writer.** Create a ServiceAccount `deployer` that can create/update/delete
   **deployments** in namespace `apps` (and nothing in any other namespace). Prove
   with `auth can-i` that it can manage deployments in `apps` but not in `default`,
   and cannot touch secrets anywhere.

2. **ClusterRole for read-only across the cluster.** Bind the built-in `view`
   ClusterRole to a new SA via a ClusterRoleBinding and verify it can list pods in
   *all* namespaces but cannot modify anything.

3. **Harden a workload.** Take the lab's failing `nginx` Pod and make it pass the
   `restricted` standard *without* changing the namespace policy. (Hint: nginx wants
   to bind port 80 as root — use an unprivileged nginx image or our `web-api`, plus a
   proper `securityContext`.)

4. **Egress policy (Calico).** On the Calico cluster, write a NetworkPolicy that
   allows `web` pods to make **DNS** queries but blocks all other egress. Verify DNS
   resolves but external/other-pod calls fail.

5. **Stretch:** Explain why granting `get secrets` cluster-wide to a workload SA is
   dangerous, and two mitigations.

## Success criteria
- [ ] `deployer` SA manages deployments only in `apps`, proven via `auth can-i`.
- [ ] A `view`-bound SA can read cluster-wide but not write.
- [ ] A hardened Pod runs in the `restricted` namespace.
- [ ] (Calico) An egress policy permits DNS while blocking other egress.
- [ ] Clear explanation of the secrets-access risk + mitigations.
