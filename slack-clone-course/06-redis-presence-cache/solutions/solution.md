# Challenge 06 — Reference Solution

### 1. Workspace presence endpoint
```python
# workspaces/views.py — on WorkspaceViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from chat import presence

@action(detail=True, methods=["get"])
def presence(self, request, pk=None):
    ws = self.get_object()
    member_ids = Membership.objects.filter(workspace=ws).values_list("user_id", flat=True)
    online = presence.online_among(member_ids)
    from accounts.models import User
    names = User.objects.filter(id__in=online).values_list("username", flat=True)
    return Response({"online": list(names)})
```
> Note: name the action method something other than the imported module (e.g.
> `presence_view`) to avoid shadowing — shown inline here for brevity.

### 2. Idle → away
```python
# chat/presence.py
AWAY_AFTER = 10

def status_of(user_id: int) -> str:
    score = _redis.zscore(ONLINE_KEY, str(user_id))
    if score is None:
        return "offline"
    age = time.time() - score
    if age <= AWAY_AFTER:
        return "online"
    if age <= PRESENCE_TTL:
        return "away"
    return "offline"
```

### 3. Per-user connection limit
```python
# chat/consumers.py — in connect(), after auth passes:
from . import presence
n = presence._redis.incr(f"conns:{self.user.id}")
if n == 1:
    presence._redis.expire(f"conns:{self.user.id}", 3600)
if n > 5:
    presence._redis.decr(f"conns:{self.user.id}")
    await self.close(code=4429)
    return
# in disconnect():
presence._redis.decr(f"conns:{self.user.id}")
```
Open 6 `wscat` clients as the same user → the 6th closes immediately.

### 4. Cache the channel list
```python
# chat/views.py — ChannelViewSet.list (override)
def list(self, request, *args, **kwargs):
    ws = request.query_params.get("workspace")
    key = f"chanlist:{request.user.id}:{ws}"
    cached = presence._redis.get(key)
    if cached:
        import json
        return Response(json.loads(cached))
    resp = super().list(request, *args, **kwargs)
    import json
    presence._redis.set(key, json.dumps(resp.data), ex=30)
    return resp

# invalidate in perform_create:
def perform_create(self, serializer):
    ...  # existing
    for k in presence._redis.scan_iter(f"chanlist:*:{serializer.instance.workspace_id}"):
        presence._redis.delete(k)
```

### 5. Fixed-window burst flaw
> A fixed window resets the counter at a hard boundary. A client can send the full
> `limit` at the very end of one window and the full `limit` again at the start of
> the next — up to **2×limit** within a moment straddling the boundary. A
> **sliding-window log** (timestamps of recent actions, count those within the last
> `window`) or a **token bucket** (tokens refill continuously at a steady rate)
> smooths this out, enforcing the rate at every instant rather than per fixed bucket.
