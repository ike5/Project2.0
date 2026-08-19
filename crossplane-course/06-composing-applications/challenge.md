# Challenge 06 — Close Every Seam

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Give the app real AWS permissions.** Right now the composition passes
   `BUCKET_NAME` to the app but no credentials, so the app couldn't actually use the
   bucket. Extend `XWebApp` so that when `storage: true` it also creates an IAM user
   with a policy scoped to *only that bucket*, generates an access key, and injects
   the key into the Deployment via a connection secret.

   Then answer honestly: why is an IAM **user** the wrong long-term answer here, and
   what would you use on a real EKS cluster? (Module 08 covers this properly — predict
   it now.)

2. **Add a worker.** Many services have a web process and a background worker sharing
   one database. Extend the composition so `spec.worker.enabled: true` adds a second
   Deployment running the same image with a different command, sharing the same
   connection secret. Both must scale independently.

3. **Make failure observable.** Delete the connection secret out from under a running
   app (`kubectl delete secret payments-db-conn -n team-payments`) and answer, with
   evidence:
   - What happens to the running Pods immediately?
   - What happens to new Pods?
   - Does Crossplane recreate the Secret? How long does it take?
   - What would a developer see, and would they be able to diagnose it?

   Then propose one change to the composition that would make this failure clearer.

4. **Draw the boundary.** Your company wants to add "the shared VPC every app runs in"
   to `XWebApp`, so each app provisions its own network. Write a short argument
   against this, and describe what you'd do instead. Reference the lifecycle test from
   the README, and be concrete about what breaks when 40 apps each own a VPC.

5. **Stretch — cross-XR composition.** An XR can compose *another XR*. Build
   `XPlatform` that composes three `XWebApp`s (a frontend, an API, and a worker) plus
   a shared bucket they all use. Then explain what makes this powerful and what makes
   it dangerous — specifically, what happens to the three apps if someone deletes the
   `XPlatform`.

## Success criteria
- [ ] `storage: true` produces working, bucket-scoped AWS credentials injected into
      the Pod, and you explained why an IAM user is the wrong long-term answer.
- [ ] `worker.enabled: true` adds an independently scalable second Deployment sharing
      the database.
- [ ] You documented all four observations from the deleted-secret experiment and
      proposed a concrete improvement.
- [ ] You wrote a reasoned argument about XR lifecycle boundaries with a concrete
      failure mode at 40 apps.
- [ ] You can explain how a connection secret removes the human from credential
      handling, in two sentences.
