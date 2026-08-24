# Challenge 19 — Operate It in Kubernetes

Solutions in [`solutions/`](./solutions/). Try first.

The lab got you a zero-drop deploy and a measured autoscaling ceiling. Both of
those are things you *configured*. This challenge is about the failures that
configuration does not reach: a worker process Kubernetes cannot see, a version
that is broken and healthy at the same time, and a second region you have to
justify to someone holding a budget.

> **Every drill runs with a load test on.** A drill without one tells you the
> cluster reconfigured; a drill with one tells you how many users noticed.

## Tasks

1. **Make a blocked worker take itself out.**
   Part D proved the liveness probe cannot see one stalled worker of four —
   twenty consecutive 200s while a quarter of the pod's connections were frozen.
   Restarting the pod is the wrong fix: it kills three healthy workers to punish
   one.

   Build the right one. The worker detects its own condition and performs a
   Module 18 drain on **itself**, closing only its own connections with a
   jittered `retry_after_ms`. Decide what signal it triggers on and defend the
   threshold — a worker that evicts itself during a normal GC pause is worse
   than the disease.

   Then handle **scale-down**, which for a socket server means choosing who gets
   disconnected. Kubernetes picks a pod by its own heuristics, not by connection
   count. Measure the disruption of the default choice, then reduce it, and be
   honest about how strong the guarantee you built actually is.

2. **Make the deploy safe when the new version is broken but healthy.**
   Ship a version that starts, passes both probes, serves traffic, and corrupts
   data. Show that `maxUnavailable: 0` does not save you, and quantify the damage
   at full rollout.

   Then build a progressive rollout with an automatic rollback trigger. At least
   one of your gating signals must be something error rate and latency cannot
   see. Prove it rolls back, and report the damage window in messages, not
   minutes.

3. **Find three Kubernetes-specific failure modes.**
   Not Module 18's drills ported over — failures that only exist because you are
   on Kubernetes. Think about evictions and QoS classes, memory limits versus
   Python's actual memory behaviour, cluster DNS, image pulls, and admission.

   At least one must reveal a real weakness in the manifests in
   [`code/k8s/`](./code/k8s/). Fix it and re-run to prove the fix.

4. **Solve sticky sessions properly, with numbers.**
   Replace one pod and count how many clients get remapped under three
   strategies: no affinity, `Service.sessionAffinity: ClientIP`, and ingress
   cookie affinity in both `balanced` and `persistent` modes.

   Then find the case where the best of those still remaps nearly everyone, and
   design something that doesn't. State what your design costs — including the
   protocol commitment and the abuse vector.

5. **Model the second region, then argue against it.**
   Produce a latency and cost model for two- and three-region deployments with
   room affinity. Include cross-region data transfer, duplicated infrastructure,
   and the engineering cost of the routing layer — and use the lab's measured
   cross-region send fraction, not an assumption.

   Then state the specific user-facing benefit, price the cheaper alternative
   that captures most of it, and give a falsifiable condition under which you
   would change your answer.

## Stretch

6. **GitOps the whole thing, with the drills as a gate.**
   Put `code/k8s/` under Argo CD or Flux, with a drill suite as a post-sync hook.
   A failing drill must block the sync and trigger a rollback.

   Then demonstrate a plausible, well-intentioned change being caught — something
   a reviewer would approve. The lab contains at least two candidates.

## Success criteria

- [ ] A worker self-evicts on a defended signal and threshold, closing only its
      own connections; false-positive rate measured over a realistic load profile
- [ ] Scale-down disruption measured for the default pod choice and reduced, with
      an honest statement of how strong the improved guarantee is
- [ ] A broken-but-healthy version rolls out fully with `maxUnavailable: 0`, with
      the damage quantified; a progressive rollout catches it on a non-availability
      signal, with the damage window measured in messages
- [ ] Three Kubernetes-specific drills run under load; at least one reveals and
      fixes a real weakness in `code/k8s/`
- [ ] Client remapping measured across four affinity configurations, a better
      design proposed, and its protocol and abuse costs stated
- [ ] Two- and three-region latency and cost models built on the measured
      cross-region send fraction, with a priced alternative and a falsifiable
      condition
- [ ] Stretch: GitOps with drills as a sync gate, catching a change a reviewer
      would have approved
