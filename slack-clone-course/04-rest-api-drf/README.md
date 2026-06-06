# Module 04 — REST API with DRF

**Goal:** expose workspaces, channels, and messages as a clean, paginated,
permission-checked REST API — the read/write surface the frontend (and the
WebSocket layer) build on.

⏱️ ~2.5 hours · 🎯 Prereq: Module 03 (auth working).

> REST handles everything that isn't a live event: listing your workspaces, loading
> a channel's history, creating a channel. Live message delivery is Module 05 — but
> messages are *created* and *read* through this API, so the two stay consistent.

---

## 1. Serializers: models ↔ JSON

A **serializer** converts model instances to JSON and validates incoming data.
Notice the patterns in `chat/serializers.py`:

- **Nested read, flat write.** `MessageSerializer` embeds the full `author`
  (`UserSerializer`) on read, but `author` is read-only — the server sets it from
  the request user, never the client.
- **Reactions are read-only nested** on a message, written through their own action.

## 2. ViewSets + routers: CRUD without boilerplate

A **ViewSet** bundles list/retrieve/create/update/destroy; a **router** generates the
URLs. `chat/urls.py` is three lines and yields a full REST surface:

```python
router.register("channels", ChannelViewSet)
router.register("messages", MessageViewSet)
```
→ `GET/POST /api/channels/`, `GET /api/messages/?channel=1`, etc.

## 3. Querysets are your security boundary

The single most important habit: **scope every queryset to what the user may see.**

```python
def get_queryset(self):
    my_ws = Membership.objects.filter(user=self.request.user).values_list("workspace_id", flat=True)
    return Channel.objects.filter(workspace_id__in=my_ws)...
```

A non-member can't list, retrieve, or guess-by-id a channel in a workspace they're
not in — the rows simply aren't in their queryset. Object-level permission classes
(`IsWorkspaceMember`) are the second layer.

## 4. Cursor pagination (for an infinite feed)

Page-number pagination breaks on a live feed: new messages shift every page. We use
**cursor pagination** ordered by `-id` — each page hands back an opaque cursor to
the next slice, stable even as new rows arrive. That's exactly how "scroll up for
older messages" works in the UI.

```
GET /api/messages/?channel=1
→ { "results": [...], "next": "cD0xMjM%3D", "previous": null }
```

## 5. Filtering

`django-filter` turns query params into safe filters:
`GET /api/messages/?channel=1&parent=42` (a thread's replies). Declared per-viewset
via `filterset_fields` — no hand-written query parsing.

## 6. Self-documenting: OpenAPI

`drf-spectacular` generates an OpenAPI schema from your serializers and viewsets.
Browse the interactive docs at `/api/schema/ui/` — the frontend team (you, in
Module 09) gets an always-current contract for free.

---

## 7. Do the lab

Drive the whole API with `curl`: create a workspace, channels, and messages; page
through history with cursors; filter a thread; and prove a second user can't see
your private channel.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

serializer · viewset · router · cursor pagination · filtering · OpenAPI

**Next →** [Module 05: Real-time with Channels](../05-realtime-channels/)
