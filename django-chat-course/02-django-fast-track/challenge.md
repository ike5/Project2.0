# Challenge 02 — Make Django Tell You the Truth

Solutions in [`solutions/`](./solutions/). Try first.

Every task here is about *seeing* what Django is doing rather than trusting it.
That habit is the difference between the two hours you will spend debugging
Module 06 and the two days.

## Tasks

1. **Make the config check itself, and prove it fails.**
   Extend `settings.py` with a startup validation block that refuses to boot when
   the configuration is internally inconsistent — not merely missing. At minimum:

   - `DEBUG=1` together with a non-loopback entry in `ALLOWED_HOSTS` is fatal,
   - `CONN_MAX_AGE > 0` together with `PG_POOLER=transaction` is fatal (Module 13
     will explain why in detail; predict the reason now and write it in the
     error message),
   - `SECRET_KEY` shorter than 40 characters is fatal when `DEBUG=0`.

   Write three one-line shell commands that each trigger exactly one of these,
   and capture the output. Then answer in two sentences: why is a Django *system
   check* (`register(Tags.security)`) a better home for two of these than a bare
   `raise` at module level — and which one does *not* belong in a system check?

2. **Find the N+1s you did not write.**
   The lab's N+1 was obvious because you wrote it. Real ones hide in serializers
   and templates. Add a `SerializerMethodField` to `RoomSerializer` that returns
   the room's three most recent message bodies, then list ten rooms and count the
   queries with `CaptureQueriesContext`.

   - Report the query count before and after `prefetch_related`.
   - Then show a case where `prefetch_related` is *worse* than `select_related`
     and explain, using the SQL, why one query with a JOIN beat two queries with
     an `IN (...)`.
   - Finally, add an `assertNumQueries` test that would have failed the day
     someone added the field. That test — not your memory — is the fix.

3. **Give the health endpoint a hard question to answer.**
   `/api/health/` currently returns 200 whenever `SELECT 1` succeeds. Split it
   into `/api/health/live/` and `/api/health/ready/` such that:

   - liveness **never** touches the database or any dependency,
   - readiness checks the database *and* reports the number of seconds since the
     last successful check, serving a cached result for up to 2 seconds so a
     health-check storm cannot become a database load test.

   Then, with the app running, `docker pause pulse-postgres` and record exactly
   what each endpoint returns and how long it takes. Write two sentences on the
   specific cascade that occurs if liveness fails when the database is down and
   an orchestrator is restarting your pods.

4. **Put a number on the async-vs-sync view difference under load.**
   Using only what you have (`curl`, `time`, and a shell loop is enough; k6 if
   you have it), produce a small table of p50/p99 wall time for the `/api/rooms/`
   list endpoint served three ways at 200 concurrent requests:

   - gunicorn, 2 sync workers
   - uvicorn, 1 worker, the view left as a normal `def` (sync, thread pool)
   - uvicorn, 1 worker, the view rewritten `async def` with `async for` over the
     queryset

   State which one wins and — this is the actual task — explain why the margin
   is **much smaller** here than the 500-connections-in-2.6-seconds result from
   Part G, and what property of this endpoint causes that.

5. **Stretch — kill the serializer on the hot path.**
   Rewrite `history` with no DRF at all: one `connection.cursor()` query, manual
   row-to-dict, and `JsonResponse`. Benchmark it against the
   `MessageSerializer` version at 50 rows and at 200 rows, 1,000 iterations
   each, and report requests/second for both.

   Then argue the other side: name three concrete things you gave up, and state
   the room size or request rate below which you would keep the serializer.
   A number, not a feeling.

## Success criteria

- [ ] Three inconsistent configurations each produce a distinct, named startup
      failure, with the system-check-vs-`raise` question answered
- [ ] A hidden serializer N+1 is measured, fixed, explained against the SQL, and
      locked down by an `assertNumQueries` test
- [ ] `live` and `ready` are split, readiness is cached, and both behaviours are
      recorded under `docker pause` with the restart cascade explained
- [ ] A p50/p99 table exists for all three server/view combinations, with the
      narrow margin explained
- [ ] Stretch: raw-cursor history is benchmarked against the serializer at two
      page sizes, with a defended crossover point
