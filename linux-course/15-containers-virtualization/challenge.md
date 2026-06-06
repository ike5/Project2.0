# Challenge 15 — Containers & Isolation

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Prove PID isolation.** Using `unshare`, start a shell in a new PID namespace and show
   that it sees itself as PID 1 and cannot see the host's processes. Explain which kernel
   feature provides this.

2. **VM vs container (short answer).** Give two reasons a container starts in
   milliseconds while a VM takes seconds, and one security advantage a VM has over a
   container.

3. **Persist data.** Run an nginx container that serves a file from a **host directory**
   (a bind mount/volume), edit the file on the host, and see the change without rebuilding
   the image. Show the `podman run -v ...` command.

4. **A two-line image.** Write a Containerfile that serves a custom `index.html` with
   nginx, build it, run it, and `curl` your page.

5. **Resource cap.** Run a container limited to 128 MB RAM and 0.25 CPU; show the command
   and how you'd verify the limits are applied. Which kernel feature enforces them?

## Success criteria
- [ ] PID-namespace shell shows PID 1 + isolated `ps`; you named *namespaces*.
- [ ] Correct VM-vs-container trade-offs.
- [ ] Bind-mounted file updates live in the running container.
- [ ] Custom nginx image serves your page.
- [ ] Capped container verified; you named *cgroups*.
