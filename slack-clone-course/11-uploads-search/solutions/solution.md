# Challenge 11 — Reference Solution

### 1. Validate uploads
```python
# chat/uploads.py — presign_upload
MAX_BYTES = 25 * 1024 * 1024
ALLOWED = {"image/png", "image/jpeg", "text/plain", "application/pdf"}

if content_type not in ALLOWED:
    return Response({"content_type": "not allowed"}, status=400)
# Return the limit; the client must respect it, and you re-check on register:
# in AttachmentViewSet.perform_create, HEAD the object and compare ContentLength.
```
```python
import boto3
def _verify_size(key):
    head = storage._client().head_object(Bucket=settings.S3_BUCKET, Key=key)
    return head["ContentLength"]
```

### 2. Indexed search vector
```python
# chat/models.py
from django.contrib.postgres.search import SearchVectorField
from django.contrib.postgres.indexes import GinIndex

class Message(models.Model):
    ...
    search = SearchVectorField(null=True)
    class Meta:
        indexes = [models.Index(fields=["channel", "-id"]),
                   GinIndex(fields=["search"], name="message_search_gin")]
```
Keep it updated on save (simple version):
```python
# after creating/updating a message
Message.objects.filter(pk=msg.pk).update(search=SearchVector("body"))
```
Query against the stored column and check the plan:
```sql
EXPLAIN ANALYZE SELECT id FROM chat_message WHERE search @@ websearch_to_tsquery('release');
-- look for "Bitmap Index Scan on message_search_gin"
```

### 3. Search in the UI
```tsx
const [results, setResults] = useState<any[]>([]);
async function run(q: string) {
  const data = await apiFetch(`/api/search/?q=${encodeURIComponent(q)}`);
  setResults(data.results);
}
// render each result linking to /w/<ws>/<channel>#msg-<id>
```

### 4. Thumbnails
```python
# notifications/tasks.py (or a media tasks module)
@shared_task
def make_thumbnail(attachment_id: int):
    from chat.models import Attachment
    from chat import storage
    a = Attachment.objects.get(id=attachment_id)
    if not a.content_type.startswith("image/"):
        return
    # download bytes, resize with Pillow, upload under f"{a.key}.thumb.jpg",
    # then a.thumb_key = ...; a.save()
```
Enqueue it from `AttachmentViewSet.perform_create` for image types.

### 5. Why presigned URLs win
> A **public bucket** exposes *every* object forever to anyone with the URL — no
> expiry, no per-user authorization. **Proxying** downloads through Django authorizes
> correctly but funnels all file bytes through your app servers, consuming workers and
> bandwidth and hurting latency. A **presigned URL** gives the client least-privilege,
> time-boxed access to exactly one object: Django authorizes the request, storage
> serves the bytes directly, and the link dies in minutes — secure *and* cheap.
