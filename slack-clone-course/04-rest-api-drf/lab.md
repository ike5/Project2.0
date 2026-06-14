# Lab 04 — Drive the API

**You'll:** create a workspace, channels, and messages over REST; page through
history with cursors; filter a thread; and prove cross-tenant isolation with a
second user.

⏱️ ~50 min. Server running from `apps/slack-backend`. Reuse the login helper from
Lab 03 to set `$ACCESS`.

```bash
ACCESS=$(curl -s -X POST localhost:8000/api/auth/login/ -H 'content-type: application/json' \
  -d '{"email":"ann@example.com","password":"slackpass123"}' | jq -r .access)
auth=(-H "Authorization: Bearer $ACCESS" -H 'content-type: application/json')
```

---

## Part A — Create a workspace (you become owner)

```bash
curl -s "${auth[@]}" -X POST localhost:8000/api/workspaces/ \
  -d '{"name":"Acme","slug":"acme"}' | jq
```
✅ Expected: `201` and `"my_role": "owner"` — `perform_create` made you the owner
in the same transaction.

```bash
curl -s "${auth[@]}" localhost:8000/api/workspaces/ | jq '.[].slug'
```
✅ You see only workspaces you belong to.

---

## Part B — Channels

```bash
WS=$(curl -s "${auth[@]}" localhost:8000/api/workspaces/ | jq '.[0].id')

curl -s "${auth[@]}" -X POST localhost:8000/api/channels/ \
  -d "{\"workspace\":$WS,\"name\":\"general\",\"kind\":\"public\"}" | jq
curl -s "${auth[@]}" -X POST localhost:8000/api/channels/ \
  -d "{\"workspace\":$WS,\"name\":\"random\",\"kind\":\"public\"}" | jq

curl -s "${auth[@]}" "localhost:8000/api/channels/?workspace=$WS" | jq '.results // . | .[].name'
```
✅ Expected: `general`, `random`.

---

## Part C — Post messages and read history

```bash
CH=$(curl -s "${auth[@]}" "localhost:8000/api/channels/?workspace=$WS" | jq '(.results // .)[0].id')

for i in $(seq 1 40); do
  curl -s "${auth[@]}" -X POST localhost:8000/api/messages/ \
    -d "{\"channel\":$CH,\"body\":\"message number $i\"}" >/dev/null
done

curl -s "${auth[@]}" "localhost:8000/api/messages/?channel=$CH" | jq '{count: (.results|length), next}'
```
✅ Expected: `count: 30` (the page size) and a non-null `next` cursor.

Follow the cursor to the next page:
```bash
NEXT=$(curl -s "${auth[@]}" "localhost:8000/api/messages/?channel=$CH" | jq -r .next)
curl -s "${auth[@]}" "$NEXT" | jq '{count: (.results|length), previous}'
```
✅ Expected: the remaining ~10 older messages, with a `previous` cursor.

---

## Part D — Threads via filtering

```bash
# reply to the newest message
NEWEST=$(curl -s "${auth[@]}" "localhost:8000/api/messages/?channel=$CH" | jq '.results[0].id')
curl -s "${auth[@]}" -X POST localhost:8000/api/messages/ \
  -d "{\"channel\":$CH,\"parent\":$NEWEST,\"body\":\"a thread reply\"}" | jq '{id, parent}'

# fetch just that thread's replies
curl -s "${auth[@]}" "localhost:8000/api/messages/?channel=$CH&parent=$NEWEST" | jq '.results[].body'
```
✅ Expected: only `a thread reply`.

---

## Part E — Prove tenant isolation

Register a second user and confirm they can't see Acme's channels:
```bash
curl -s -X POST localhost:8000/api/auth/register/ -H 'content-type: application/json' \
  -d '{"email":"bob@example.com","username":"bob","password":"slackpass123"}' >/dev/null
BOB=$(curl -s -X POST localhost:8000/api/auth/login/ -H 'content-type: application/json' \
  -d '{"email":"bob@example.com","password":"slackpass123"}' | jq -r .access)

curl -s -H "Authorization: Bearer $BOB" "localhost:8000/api/channels/?workspace=$WS" | jq
curl -s -o /dev/null -w "%{http_code}\n" -H "Authorization: Bearer $BOB" \
  localhost:8000/api/channels/$CH/
```
✅ Expected: an empty list, then `404` — bob isn't a member, so the rows aren't in
his queryset at all.

---

## What you learned
- Serializers + viewsets + routers give a full REST surface with little code.
- The queryset is the security boundary; non-members literally can't see rows.
- Cursor pagination yields stable "scroll for older" over a live feed.
- `django-filter` powers thread queries via `?parent=`.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 05](../05-realtime-channels/).
