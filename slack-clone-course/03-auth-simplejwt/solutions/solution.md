# Challenge 03 — Reference Solution

### 1. 2-minute access token
```python
# config/settings.py
SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"] = timedelta(minutes=2)
```
Log in, wait >2 min, then:
```bash
curl -s -o /dev/null -w "%{http_code}\n" localhost:8000/api/auth/me/ \
  -H "Authorization: Bearer $ACCESS"          # 401 (expired)
curl -s -X POST localhost:8000/api/auth/refresh/ -H 'content-type: application/json' \
  -d "{\"refresh\":\"$REFRESH\"}" | jq -r .access   # a fresh, working access token
```

### 2. `IsSelf` / read-only fields
`MeView.get_object()` already returns `request.user`, so you can never address
another user. Read-only fields can't change:
```bash
curl -s -X PATCH localhost:8000/api/auth/me/ -H "Authorization: Bearer $ACCESS" \
  -H 'content-type: application/json' -d '{"id": 999, "email":"x@y.z"}' | jq
# id and email are unchanged — they're read_only in UserSerializer
```
If you want an explicit class:
```python
class IsSelf(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user
```

### 3. Staff-only endpoint
```python
# accounts/views.py
from rest_framework.permissions import IsAdminUser

class AdminPingView(APIView):
    permission_classes = [IsAdminUser]   # is_staff required
    def get(self, request):
        return Response({"pong": True})
```
```python
# accounts/urls.py
path("admin-ping/", AdminPingView.as_view()),
```
Staff → `200 {"pong": true}`; normal user → `403`.

### 4. Throttle login
```python
# config/settings.py
REST_FRAMEWORK["DEFAULT_THROTTLE_RATES"]["anon"] = "5/min"
```
```bash
for i in $(seq 1 6); do
  curl -s -o /dev/null -w "%{http_code}\n" -X POST localhost:8000/api/auth/login/ \
    -H 'content-type: application/json' -d '{"email":"ann@example.com","password":"wrong"}'
done
# the 6th prints 429
```

### 5. Signature vs blacklist
> Access tokens are verified by checking their **signature** only — fast and
> stateless, so any backend Pod can validate one without a database hit. The cost is
> that a still-valid access token *cannot* be revoked instantly; it stays usable
> until it expires (which is why we keep its lifetime short, ~15 min). The refresh
> token, used rarely, is checked against a database **blacklist**, so logout/rotation
> can truly kill it.
