# Challenge 05 — Wire Up Networking

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Diagnose a dead Service.** Apply the provided `broken-service.yaml`. `curl`ing
   it from a client Pod fails. Find out *why* using `kubectl get endpoints` and
   `--show-labels`, then fix it (one-line change) so it serves traffic.

2. **Cross-namespace discovery.** Put a `web` Deployment+Service in namespace
   `team-a` and a client Pod in `default`. From the client, reach the service using
   its **fully-qualified DNS name**. Write down the FQDN you used.

3. **Host-based Ingress.** Add an Ingress rule that routes the host
   `web.localdev.me` to your `web` Service (`web.localdev.me` resolves to 127.0.0.1
   automatically). Verify with `curl -H 'Host: web.localdev.me' http://localhost/`.

4. **Stretch:** Explain the difference between a Service's `port` and `targetPort`,
   and what happens if `targetPort` doesn't match the container's listening port.

## Success criteria
- [ ] You identified the selector/label mismatch in `broken-service.yaml` and fixed it.
- [ ] You reached a Service across namespaces via its FQDN.
- [ ] A host-based Ingress rule routes `web.localdev.me` to `web`.
- [ ] You can explain `port` vs `targetPort`.
