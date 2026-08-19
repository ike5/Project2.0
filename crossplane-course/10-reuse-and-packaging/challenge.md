# Challenge 10 — Ship It

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Package your whole platform.** Build a real Configuration containing every API
   you've written: `XNetwork` (07), `XAppIdentity` (08), and `XDatabase` (09). Get
   `dependsOn` right, build it, and install it on a *clean* cluster
   (`delete-cluster.sh && create-cluster.sh`, then Crossplane, then your package).

   Success is: from a fresh cluster, one `Configuration` object gets you a working
   platform, with no manual provider or function installation.

2. **Publish two versions and prove the difference.** Tag your package `v1.0.0`.
   Then make a genuinely backward-compatible change (add an optional field with a
   default), tag it `v1.1.0`, and upgrade a cluster with existing XRs. Show that
   nothing was recreated.

   Then make the *rename* change from Lab Part H, tag it `v2.0.0`, and show what
   upgrading does. Write the release notes you'd publish for `v2.0.0`.

3. **Make the environment un-spoofable.** In Part C, a developer picks their
   environment with `spec.environment: prod`. Nothing stops a dev-namespace developer
   selecting the prod EnvironmentConfig and getting a role in the production account.

   Fix it so the environment is derived from something the developer **cannot set**.
   (Hint: namespace labels plus `function-extra-resources`, or an admission policy.)
   Implement it and demonstrate the attack failing.

4. **Automate `Usage`.** Writing `Usage` objects by hand doesn't scale. Extend the
   `XNetwork` composition so it emits `Usage` objects declaring that each subnet uses
   the VPC, and each route table association uses its subnet.

   Then measure it: time a teardown with and without them, and report both numbers.

5. **Stretch — a dependency conflict.** Create two Configuration packages that depend
   on incompatible versions of the same provider (`>=v1.21.0` and `<v1.20.0`). Install
   both, observe what Crossplane does, and explain how you'd resolve it. Then explain
   why `dependsOn` should use ranges rather than exact pins.

## Success criteria
- [ ] One `Configuration` object on a fresh cluster yields a working platform with all
      three APIs.
- [ ] `v1.1.0` upgrades cleanly with nothing recreated; `v2.0.0` demonstrably
      recreates resources, and your release notes say so prominently.
- [ ] A developer in a dev namespace cannot obtain a prod-account role, and you
      demonstrated the failure.
- [ ] `XNetwork` emits its own `Usage` objects, with before/after teardown timings.
- [ ] You can explain why renaming a composed resource is a major version bump.
