# Challenge 00 — Know Your Tools

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Create a table by hand.** Using `psql` in the Postgres container, create a
   throwaway table `ping (id serial primary key, note text)`, insert one row, and
   `SELECT *` it back. Then `DROP` it.

2. **Make Redis forget.** Set a key `flash` to any value with a **10-second**
   expiry in a single command, immediately read it, wait 11 seconds, and confirm
   it's gone (`GET` returns `(nil)`).

3. **Survive a restart.** Stop the Postgres container, start it again, and prove
   your `slack` database still exists. Explain in one sentence *why* the data
   survived.

4. **Inspect the cluster.** Recreate the kind cluster and answer: how many nodes
   are there, which one is the control-plane, and what command shows the system
   Pods running on them?

5. **Stretch:** Without re-running it, explain what would happen if you ran
   `create-cluster.sh` a second time while the cluster already exists — and why
   the script is written to be safe.

## Success criteria
- [ ] You created, queried, and dropped a table in the `slack` database.
- [ ] A Redis key with a 10s TTL expired on its own.
- [ ] Postgres data survived a container restart, and you can say why.
- [ ] You can state the node count and identify the control-plane node.
- [ ] You can explain why re-running the create script is harmless (idempotent).
