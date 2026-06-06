# Challenge 04 — Round Out the API

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Add a reactions endpoint.** Add a viewset action or nested route so a user can
   `POST` an emoji reaction to a message and `DELETE` their own. Enforce the
   `uniq_reaction` rule gracefully (return `400`, not a `500`).

2. **Edit and delete messages.** Allow a message's **author** to `PATCH` its body
   (set `edited_at = now()`) and `DELETE` it. A different user attempting either gets
   `403`.

3. **Join a public channel.** Add a `POST /api/channels/{id}/join/` action that
   creates a `ChannelMember` for the requesting user (only for `public` channels in a
   workspace they belong to).

4. **Search-ish filter.** Add a `?q=` filter on messages that returns messages whose
   `body` contains the term (case-insensitive). (Real full-text search is Module 11;
   this is the simple `icontains` version.)

5. **Stretch:** Explain why we use **cursor** pagination for messages but ordinary
   page-number pagination would be fine for the workspace **members** list.

## Success criteria
- [ ] React/unreact works and duplicates return `400`.
- [ ] Only the author can edit/delete a message; others get `403`.
- [ ] A user can join a public channel via the action.
- [ ] `?q=` filters messages by substring.
- [ ] You can justify cursor vs page-number pagination per resource.
