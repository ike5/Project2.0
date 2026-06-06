# Challenge 07 — Production-grade Async

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Welcome email on signup.** When a user registers, enqueue a `send_welcome_email`
   task. Confirm registration still returns instantly (the email is sent by the worker).

2. **Invite flow.** Wire `send_invite_email` to fire when an `Invite` is created
   (e.g. a workspace admin invites `new@example.com`). Verify the email contains the
   accept link with the token.

3. **Don't notify yourself.** Prove that mentioning *yourself* (`@ann` in ann's own
   message) creates no notification and sends no email.

4. **A dedicated queue.** Route `send_email` to its own Celery queue named `email`
   and run a worker that consumes only that queue. Explain why isolating email onto
   its own queue/worker is useful in production.

5. **Stretch:** `fan_out_message` re-fetches the message by id. Describe the race
   where the task runs *before* the surrounding DB transaction commits, and how
   `transaction.on_commit(...)` (or `CELERY_TASK_ALWAYS_EAGER` in tests) avoids
   enqueuing work that references uncommitted rows.

## Success criteria
- [ ] Signup enqueues a welcome email without slowing the response.
- [ ] Creating an invite sends an email with the token link.
- [ ] Self-mentions produce no notification/email.
- [ ] `send_email` runs on a dedicated `email` queue/worker.
- [ ] You can explain the on_commit race and its fix.
