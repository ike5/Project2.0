# Challenge 14 — The Production-Ready Image

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Reduce image size.** Rebuild the image and check the size
   (`docker images taskforge`). Try `eclipse-temurin:21-jre-alpine` and
   compare. Document the trade-off (smaller vs musl libc quirks).

2. **Run as a non-root user.** Confirm the process inside the container
   isn't root: `docker compose exec app id`. (It should be `uid=1000(app)`.)

3. **Healthcheck for the data services.** Add a `healthcheck` to Postgres,
   Redis, and Kafka. `app` should `depends_on: { postgres: { condition:
   service_healthy } }` so it doesn't start until the DB is ready.

4. **Externalize all secrets.** Move the JWT secret, DB password, and
   MinIO password to a `.env` file. Reference them in `docker-compose.yml`
   as `${VAR}`. Confirm the app reads them at startup.

5. **Resource limits.** Add `mem_limit: 512m` and `cpus: "1.0"` to the
   `app` service. Confirm Docker enforces them with
   `docker stats taskforge-app-1`.

6. **Multi-arch build.** Use `docker buildx` to build the image for both
   `linux/amd64` and `linux/arm64`. (Useful if your laptop is Apple
   Silicon and the server is x86.)

7. **Stretch:** Add a `Makefile` with `make up`, `make down`, `make logs`,
   `make build`, and `make test` (runs the Maven tests). Make the team's
   daily commands one-liners.

## Success criteria

- [ ] Image size documented; the alpine variant is noticeably smaller.
- [ ] The app process runs as a non-root user.
- [ ] Data services have healthchecks; `app` waits for them.
- [ ] All secrets come from a `.env` file.
- [ ] Resource limits are set and visible in `docker stats`.
- [ ] A multi-arch build succeeds.
- [ ] Stretch: a `Makefile` is committed.
