# Challenge 12 — Operate Like Production

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Quota enforcement proof.** In a fresh namespace with a ResourceQuota of
   `requests.cpu: "1"` and **no** LimitRange, try to create a Pod that sets no
   requests. Observe the rejection and explain why a LimitRange fixes it.

2. **Tighten a rollout.** Add a PodDisruptionBudget (`minAvailable: 80%`) to a
   5-replica Deployment, then drain a node and confirm evictions never drop below 4
   available Pods.

3. **GitOps change flow.** Through Argo CD, change the `gitops-web` app's replica
   count the *correct* way: edit the manifest in Git, push, and watch Argo CD sync.
   Then perform a rollback using `git revert` and confirm the cluster follows.

4. **App-of-apps (stretch).** Read about Argo CD's "app of apps" pattern and sketch
   how you'd manage *multiple* applications from a single root Application.

5. **Explain:** Why is GitOps safer than running `kubectl apply` from a CI pipeline
   that holds cluster admin credentials? Give two concrete reasons.

## Success criteria
- [ ] You triggered a quota rejection and explained the LimitRange remedy.
- [ ] PDB kept ≥4/5 Pods available during a drain.
- [ ] You changed and rolled back the app via Git commits (not `kubectl`).
- [ ] You can articulate GitOps security/auditability advantages.
