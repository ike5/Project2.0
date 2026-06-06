# Challenge 06 — Tune the Hot Path

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Workspace presence endpoint.** Add `GET /api/workspaces/{id}/presence/` that
   returns the usernames of members who are currently online (use
   `presence.online_among` against the workspace's member ids).

2. **Idle → away.** Introduce a third state. If a user's last heartbeat is older than
   10 s but newer than 30 s, report them as `away` instead of `online`/`offline`.
   Return a status string per user.

3. **Per-IP connection limit.** Reject a WebSocket `connect` if the same user has
   opened more than 5 simultaneous connections (hint: track a count in Redis on
   connect/disconnect). Prove it rejects the 6th.

4. **Cache a hot read.** The channel list for a workspace is requested constantly.
   Cache `GET /api/channels/?workspace=X` results in Redis for 30 s, and invalidate
   the cache when a channel is created in that workspace.

5. **Stretch:** Your fixed-window limiter allows a burst at a window boundary (10 at
   9.9 s + 10 at 10.1 s = 20 in a blink). Explain this flaw and describe how a
   sliding-window or token-bucket approach fixes it.

## Success criteria
- [ ] A presence endpoint lists online workspace members.
- [ ] Users show online / away / offline based on heartbeat age.
- [ ] The 6th simultaneous connection for a user is rejected.
- [ ] Channel lists are cached and invalidated on create.
- [ ] You can explain the fixed-window burst flaw and a better algorithm.
