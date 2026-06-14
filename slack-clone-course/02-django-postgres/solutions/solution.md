# Challenge 02 — Reference Solution

### 1. Add `is_archived` to Channel
```python
# chat/models.py — inside class Channel
is_archived = models.BooleanField(default=False)
```
```bash
python manage.py makemigrations chat
python manage.py migrate
docker compose -f ../../00-setup/compose.dev.yml exec postgres \
  psql -U slack -d slack -c '\d chat_channel' | grep is_archived
```

### 2. Pin a message
```python
# chat/models.py — inside class Message
pinned = models.BooleanField(default=False)
```
```bash
python manage.py makemigrations chat && python manage.py migrate
```
```python
# shell
from chat.models import Message
m = Message.objects.first()
m.pinned = True
m.save(update_fields=["pinned"])
```

### 3. Latest 5 with authors, no N+1
```python
from chat.models import Channel, Message
ch = Channel.objects.get(name="general")
qs = (
    Message.objects
    .filter(channel=ch)
    .select_related("author")     # JOINs author in one query → no N+1
    .order_by("-id")[:5]
)
for m in qs:
    print(m.author.username, m.body)
```
> `select_related("author")` follows the FK with a SQL JOIN, so accessing
> `m.author.username` doesn't fire an extra query per row.

### 4. Prove the reaction constraint
```python
from django.db import IntegrityError, transaction
from chat.models import Reaction, Message
from accounts.models import User

m = Message.objects.first()
u = User.objects.first()
Reaction.objects.create(message=m, user=u, emoji="👍")
try:
    with transaction.atomic():
        Reaction.objects.create(message=m, user=u, emoji="👍")   # duplicate
except IntegrityError as e:
    print("blocked by uniq_reaction:", e)
```

### 5. Why a `through` model
> A plain `ManyToManyField` can only store the *link* between a user and a
> workspace — it has nowhere to put extra data. We need each link to carry a `role`
> (owner/admin/member) and a `joined_at`, plus a uniqueness constraint, so we make
> the join table explicit with `through="Membership"` and add those fields to it.
