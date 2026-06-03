# Challenge 08 — Control Placement & Scale

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Pin to a node.** Label one worker `tier=hot`, then schedule a Deployment so its
   Pods run **only** on that node using `nodeSelector`. Verify with `-o wide`.

2. **Hard spread.** Modify the spread Deployment to use **required** (not preferred)
   podAntiAffinity. Scale it to 3 on your 2-worker cluster and explain what happens
   to the 3rd Pod and why.

3. **Topology spread.** Use `topologySpreadConstraints` (maxSkew 1 over
   `kubernetes.io/hostname`) to evenly distribute 4 replicas, and confirm the
   distribution.

4. **Tune an HPA.** Create an HPA for `web` targeting **70%** CPU, min 2, max 6.
   Drive load and record the replica count at steady state. Then explain why the HPA
   would never scale if you forgot `resources.requests.cpu`.

5. **Stretch:** Cordon a worker node (`kubectl cordon`), trigger a rollout, and
   observe Pods avoiding it; then `uncordon`. How does cordon differ from a taint?

## Success criteria
- [ ] Pods pinned to the labeled node via nodeSelector.
- [ ] Required anti-affinity leaves the 3rd Pod `Pending`; you can explain why.
- [ ] 4 replicas evenly spread via topologySpreadConstraints.
- [ ] HPA tuned to 70%/2/6 and you can explain the requests dependency.
