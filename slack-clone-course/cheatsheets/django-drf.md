# Cheatsheet — Django & DRF

Quick reference for the backend. Keep it open while you build.

## manage.py (the commands you'll use 100×)

```bash
python manage.py runserver              # dev server (ASGI via daphne)
python manage.py makemigrations [app]   # write migration files from model changes
python manage.py migrate                # apply migrations to the DB
python manage.py makemigrations --check --dry-run   # CI: fail if models drifted
python manage.py createsuperuser        # admin login
python manage.py shell                  # interactive ORM shell
python manage.py changepassword <user>
python manage.py collectstatic --noinput
python manage.py dbshell                # raw psql against the configured DB
```

## ORM essentials

```python
Message.objects.filter(channel=ch).order_by("-id")[:30]     # latest 30
Message.objects.filter(channel=ch).select_related("author") # JOIN FK → no N+1
Channel.objects.prefetch_related("messages")                # batch reverse/M2M
qs.values_list("id", flat=True)                             # just the ids
qs.annotate(n=Count("messages")).filter(n__gt=0)            # aggregate + filter
Membership.objects.get_or_create(user=u, workspace=w)       # idempotent create
.exists()  .count()  .first()  .update(field=…)  .delete()
```

## Constraints & indexes (in Meta)

```python
class Meta:
    constraints = [models.UniqueConstraint(fields=["a", "b"], name="uniq_a_b")]
    indexes = [models.Index(fields=["channel", "-id"])]
    ordering = ["id"]
```

## DRF building blocks

```python
# serializer: nested read, server-set fields read-only
class MessageSerializer(ModelSerializer):
    author = UserSerializer(read_only=True)
    class Meta: model = Message; fields = (...); read_only_fields = ("author",)

# viewset: scope the queryset = security boundary
class MessageViewSet(ModelViewSet):
    def get_queryset(self):
        return Message.objects.filter(channel__workspace__members=self.request.user)
    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

# router
router.register("messages", MessageViewSet, basename="message")
```

## Permissions, pagination, filtering

```python
permission_classes = [IsAuthenticated, IsWorkspaceMember]
pagination_class = CursorPagination          # set ordering = "-id"
filterset_fields = ["channel", "parent"]     # ?channel=1&parent=42
```

## SimpleJWT

```
POST /api/auth/login/    {email,password}   → {access, refresh, user}
POST /api/auth/refresh/  {refresh}          → {access, refresh}  (rotates)
POST /api/auth/logout/   {refresh}          → 205 (blacklists)
Header on every call:  Authorization: Bearer <access>
```

## Quick debugging

```python
from django.db import connection; print(connection.queries[-1])   # last SQL
str(queryset.query)                                               # the SQL a qs will run
```
