# Challenge 06 — Persistent Workloads

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Persistent web content.** Run an nginx Deployment whose
   `/usr/share/nginx/html` is backed by a PVC. Write a custom `index.html` into the
   volume, then delete and recreate the Pod and confirm nginx still serves your page.

2. **Shared scratch between containers.** Build a single Pod with two containers
   that share an `emptyDir`: one writes a timestamp every second to a file, the
   other tails that file. Show that they see the same file.

3. **Observe the binding lifecycle.** Create a PVC and inspect: its STATUS before a
   Pod uses it, the PV that backs it, the PV's reclaim policy, and what happens to
   the PV when you delete the PVC.

4. **Stretch:** Explain why `ReadWriteOnce` is usually fine for a single-replica
   database but problematic if you naively scale that Deployment to 3 replicas, and
   what object type you'd reach for instead (hint: next module).

## Success criteria
- [ ] nginx serves your custom page that survives Pod recreation (PVC-backed).
- [ ] Two containers in one Pod share data via `emptyDir`.
- [ ] You described the PVC→PV binding and reclaim behavior.
- [ ] You can explain the RWO + multi-replica problem.
