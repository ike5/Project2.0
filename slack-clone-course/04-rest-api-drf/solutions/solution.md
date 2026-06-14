# Challenge 04 — Reference Solution

### 1. React / unreact
```python
# chat/views.py — on MessageViewSet
from rest_framework import status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import IntegrityError
from .models import Reaction

@action(detail=True, methods=["post", "delete"])
def react(self, request, pk=None):
    message = self.get_object()
    emoji = request.data.get("emoji")
    if not emoji:
        return Response({"emoji": "required"}, status=400)
    if request.method == "DELETE":
        Reaction.objects.filter(message=message, user=request.user, emoji=emoji).delete()
        return Response(status=204)
    try:
        Reaction.objects.create(message=message, user=request.user, emoji=emoji)
    except IntegrityError:
        return Response({"detail": "already reacted"}, status=400)  # not a 500
    return Response(status=201)
```

### 2. Author-only edit/delete
```python
# add UpdateModelMixin, DestroyModelMixin to MessageViewSet's bases, then:
from django.utils import timezone
from rest_framework.exceptions import PermissionDenied

def _ensure_author(self, obj):
    if obj.author_id != self.request.user.id:
        raise PermissionDenied("Only the author can modify this message.")

def perform_update(self, serializer):
    self._ensure_author(serializer.instance)
    serializer.save(edited_at=timezone.now())

def perform_destroy(self, instance):
    self._ensure_author(instance)
    instance.delete()
```

### 3. Join a public channel
```python
# chat/views.py — on ChannelViewSet
from .models import ChannelMember
from workspaces.permissions import is_member

@action(detail=True, methods=["post"])
def join(self, request, pk=None):
    channel = self.get_object()
    if channel.kind != "public" or not is_member(request.user, channel.workspace_id):
        return Response({"detail": "cannot join"}, status=403)
    ChannelMember.objects.get_or_create(channel=channel, user=request.user)
    return Response(status=204)
```

### 4. `?q=` substring filter
```python
# chat/views.py — MessageViewSet.get_queryset(), before returning:
q = self.request.query_params.get("q")
if q:
    qs = qs.filter(body__icontains=q)
```

### 5. Cursor vs page-number
> Messages are an **append-heavy, frequently-changing** feed: with page numbers,
> new messages arriving between requests shift every row, so "page 2" returns
> overlapping/duplicated results. Cursor pagination anchors to a row id, so paging is
> stable. The **members** list is small and changes rarely, so page numbers are
> perfectly fine and even nicer for a "page 3 of 5" UI.
