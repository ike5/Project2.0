# Challenge 14 — Make Git the Only Way In

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Close the last door.** GitOps is only a control if nobody can bypass it. Using
   Module 13's RBAC, configure the cluster so that **only Argo CD's service account**
   can create or modify XRDs, Compositions, and providers — no human, including you.

   Then answer: how do you make an emergency change when Argo CD itself is broken?
   Design that path and explain why it's safe.

2. **Promote across environments.** Build a three-environment structure (dev, staging,
   prod) where promotion is bumping a pinned Configuration version. Demonstrate
   promoting `v1.0.0` → `v1.1.0` through all three, and show that prod stays on the
   old version until deliberately moved.

   Then explain why pinning a **version** beats tracking a **branch**.

3. **Detect real drift, not noise.** With `ignoreDifferences` on
   `/spec/forProvider`, Argo CD now ignores *all* changes there — including ones a
   human made in the console that Crossplane hasn't corrected yet.

   Design something better: a check that distinguishes late-initialization noise from
   genuine unauthorized change. Be honest about what it can and can't tell apart.

4. **Test what CI can't.** Every check in this module is static. Write an end-to-end
   test that runs against a real (kind) cluster in CI: applies an XR, waits for it to
   be ready, **uses the output the way an application would**, and tears down.

   This is the only thing that catches the Module 12 Stack 5 class — explain why.

5. **Stretch — the whole pipeline.** Assemble everything into one repo with working CI:
   render, validate, consistency, IAM lint, destructive-change gate, and the e2e test
   from Task 4, publishing a versioned package on merge to main. Run it end to end.

## Success criteria
- [ ] Humans cannot modify XRDs, Compositions, or providers directly; you designed and
      justified a break-glass path for when Argo CD is down.
- [ ] Three environments promote by pinned version, and you argued version-over-branch.
- [ ] Your drift check distinguishes late-init from unauthorized change, with stated
      limits.
- [ ] A working e2e test that consumes the XR's output, and an explanation of why
      static checks cannot replace it.
- [ ] You can explain why the destructive-rename check is worth more than every other
      check combined.
