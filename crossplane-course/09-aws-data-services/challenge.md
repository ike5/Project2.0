# Challenge 09 — A Database API You'd Trust in Production

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Add read replicas.** Extend `XDatabase` with `spec.readReplicas` (0–5). Each
   replica is an `Instance` with `replicateSourceDb` pointing at the primary. Publish
   a `DATABASE_READ_HOST` connection detail pointing at the first replica, falling
   back to the primary when there are none — so applications can always use it.

   Then explain why replicas must be created *after* the primary is available, and how
   your composition handles that without `function-sequencer`.

2. **Build a `DATABASE_URL`.** Applications usually want one connection string, not
   five variables. Publish
   `postgres://user:password@host:port/dbname?sslmode=require` as a connection detail.

   This is harder than it looks: the password must be URL-encoded, and
   `connectionDetails` can't concatenate. Solve it, and explain where the value has to
   be assembled.

3. **Rotate the password.** Design and implement password rotation for a running
   database with no application downtime. Consider: what generates the new password,
   how does the database learn it, how does the app pick it up, and what happens to
   in-flight connections?

   Be honest about which parts Crossplane handles and which it doesn't.

4. **Survive a real outage.** Your `payments-db` in production has been deleted by
   someone running `kubectl delete xdatabase` in the wrong context. Walk through, with
   actual commands:
   - What state is the AWS resource in, given the composition's prod settings?
   - Exactly how do you recover it?
   - How do you bring the recovered database back under Crossplane management?
   - What would you change so this can't happen again?

5. **Stretch — multi-engine.** Support `engine: mysql` properly: different default
   version, different port (3306), different `pg_isready` equivalent, and a
   `DATABASE_URL` with a `mysql://` scheme. Then argue whether supporting two engines
   in one composition is a good idea, or whether two separate compositions selected by
   label would be better.

## Success criteria
- [ ] `readReplicas: 2` produces two working replicas and a `DATABASE_READ_HOST` that
      is correct with zero replicas too.
- [ ] `DATABASE_URL` is published, correctly URL-encoded, and you explained where it
      must be assembled and why.
- [ ] You designed a rotation procedure and stated plainly which parts Crossplane
      does not solve.
- [ ] Your outage walkthrough has real commands and a concrete prevention change.
- [ ] You can name the three independent deletion protections and which layer each
      operates at.
