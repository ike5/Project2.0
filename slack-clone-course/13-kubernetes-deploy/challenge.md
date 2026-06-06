# Challenge 13 — Operate the Deployment

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Roll out a change.** Change a string in the backend (e.g. the health payload),
   rebuild + `kind load` a new tag, update the web image, and watch a **zero-downtime**
   rolling update (`kubectl rollout status`). Then `kubectl rollout undo` it.

2. **Scale by hand.** Scale `web` to 4 replicas with `kubectl scale`, confirm the
   Service load-balances across them (curl the health endpoint repeatedly and observe
   different pod hostnames if you add one to the response).

3. **Read the config the right way.** Change `FRONTEND_ORIGIN` in the ConfigMap and
   get the web pods to pick it up. Explain why editing a ConfigMap doesn't restart pods
   and how `kubectl rollout restart` fixes it.

4. **Break it on purpose.** Set the web image to a nonexistent tag and observe the
   failure mode (`ImagePullBackOff`). Fix it and explain what `imagePullPolicy` and
   `kind load` have to do with it.

5. **Stretch:** The beat Deployment uses `replicas: 1` + `Recreate`. Explain precisely
   what goes wrong if you set it to 2, and why web/worker don't have that problem.

## Success criteria
- [ ] A rolling update deployed and rolled back with no downtime.
- [ ] `web` scaled and the Service balanced across replicas.
- [ ] A ConfigMap change took effect after a rollout restart, and you can say why.
- [ ] You reproduced and fixed `ImagePullBackOff`.
- [ ] You can explain why beat must be a singleton.
