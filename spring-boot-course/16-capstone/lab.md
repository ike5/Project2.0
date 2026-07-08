# Lab 16 — The Capstone

There is no step-by-step this time. The module **README** is the lab.

Pick three exercises from the README's §2 and complete them. For each,
record the artifact that proves it works:

| Exercise | Proof |
|----------|-------|
| A — Deploy the full stack | `docker compose ps` shows all services healthy |
| B — Run the smoke test | Output of every check in [VERIFY.md](../VERIFY.md) |
| C — A real workflow | The end-to-end transcript (token issuance, create, email, 403, complete) |
| D — Failure drill | `/actuator/health` flipping DOWN → UP, with timestamps |
| E — Trace a slow request | Screenshot of the Zipkin trace |
| F — Capacity test | A Grafana panel screenshot of p99, RPS, pool, JVM |
| G — A new feature | The PR description, the `git diff` summary, the tests |

Commit the proofs to `spring-boot-course/16-capstone/proofs/`:

```
16-capstone/proofs/
├── A-deploy.txt
├── B-smoke-test.txt
├── C-workflow.txt
├── D-failure-drill.txt
├── E-trace.png
├── F-load-test.png
└── G-comments-feature.md
```

When you're done, post a summary in your team's channel (or your own
notes):

- One sentence per module: "what I built."
- One sentence on the most useful thing you learned.
- One sentence on the next thing you want to dig into.
