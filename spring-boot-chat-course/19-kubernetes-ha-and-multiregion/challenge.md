# Challenge 19 — Operate It in Kubernetes

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Autoscale a socket server.**
   HPA on CPU is wrong for Pulse — a node holding 10,000 idle connections uses
   little CPU but has no capacity left. Design and implement autoscaling on a
   metric that actually reflects capacity.

   Then handle scale-*down*, which for a socket server means disconnecting
   people. Measure the disruption and minimize it.

2. **Make the deploy safe when the new version is broken.**
   Ship a version that starts, passes health checks, and then corrupts messages.
   Show that `maxUnavailable: 0` does not save you.

   Implement a progressive rollout with an automatic rollback trigger based on a
   real signal. Prove it rolls back before significant damage.

3. **Find three Kubernetes-specific failure modes.**
   Run drills that only exist in Kubernetes — not the Compose ones ported over.
   Think about: evictions, resource limits, DNS, the API server, and image pulls.

   At least one should reveal a real weakness in your manifests.

4. **Solve sticky sessions properly.**
   Cookie affinity at the ingress breaks when pods change. Measure how many
   clients are remapped when one pod is replaced, and compare against
   `sessionAffinity: ClientIP` and no affinity.

   Then design something better, and say what it costs.

5. **Model the multi-region cost.**
   Produce a real cost and latency model for two- and three-region deployments
   with room affinity. Include data transfer, duplicated infrastructure, and the
   engineering cost of the routing layer.

   Then state the specific user-facing benefit and whether it justifies the cost.

6. **Stretch — GitOps the whole thing.**
   Put the manifests under Argo CD or Flux, with the drill suite from Module 18
   as a post-sync hook. A failing drill must block the sync.

   Then demonstrate a bad change being caught before it reaches production.

## Success criteria

- [ ] Autoscaling keys off a capacity-reflecting metric; scale-down disruption is
      measured and minimized
- [ ] A broken-but-healthy version is shown to roll out fully; a progressive
      rollout with automatic rollback catches it, with the damage window measured
- [ ] Three Kubernetes-specific drills run; at least one reveals and fixes a real
      manifest weakness
- [ ] Client remapping measured across three affinity strategies, with a better
      design proposed and costed
- [ ] A two- and three-region cost/latency model with a stated user benefit and a
      verdict
- [ ] Stretch: GitOps with drills as a sync gate, catching a bad change
