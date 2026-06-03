# Challenge 01 — Make It Yours

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Build a v2.** Change the default `GREETING` in `apps/web-api/app.py` to
   something of your own, build it as `web-api:2.0`, and run it locally with Docker.
   Confirm `curl localhost:8080/` shows your new greeting.

2. **Override config without rebuilding.** Run `web-api:1.0` (the original) but make
   it report `color=purple` and `version=9.9.9` using **only** `docker run` flags —
   no rebuild. Verify via `/config`.

3. **Inspect like a pro.** While a container is running, find:
   - the user the process runs as,
   - the value of the `PORT` env var,
   - the container's logs.

4. **Load v2 into kind** and run it as a Pod named `web2`. Reach it with
   `port-forward` and confirm your new greeting appears. (Don't forget the local-image gotcha.)

5. **Stretch:** Without looking it up again, explain in one sentence why
   `kubectl run web2 --image=web-api:2.0` *without* `imagePullPolicy: Never` would
   fail on kind.

## Success criteria
- [ ] `web-api:2.0` exists in `docker images` and serves your custom greeting.
- [ ] You configured color/version at *run time* via `-e` flags.
- [ ] You retrieved the run-as user, `PORT`, and logs of a running container.
- [ ] A `web2` Pod runs in the cluster and you reached it with port-forward.
- [ ] You can explain the local-image / `imagePullPolicy: Never` gotcha.
