# Module 11 — File Uploads & Search

**Goal:** let users attach files (uploaded straight to object storage via presigned
URLs) and search message history with Postgres full-text search.

⏱️ ~3 hours · 🎯 Prereq: Module 04 (REST API). MinIO + Postgres running.

> Two features that look small but teach big production patterns: never proxy file
> bytes through your app, and never `LIKE '%...%'` your way through search.

---

## 1. The presigned-upload pattern

Routing megabytes of file data through Django would tie up workers and waste
bandwidth. Instead, the **browser uploads directly to storage**, and Django only
brokers permission:

```
1. browser → Django:  POST /api/uploads/presign/  {filename, content_type}
2. Django  → browser: { key, upload_url }          (a short-lived signed PUT URL)
3. browser → MinIO/S3: PUT upload_url  (the raw bytes — Django never sees them)
4. browser → Django:  POST /api/attachments/ {key, filename, size, message}
5. browser → Django:  POST /api/messages/  referencing the attachment
```

Django mints the URL with `boto3.generate_presigned_url` (`chat/storage.py`). The URL
embeds a signature and expires in minutes, so it can't be reused or shared. The
upload **key** is namespaced and random (`u/<user>/<uuid>/<name>`) so users can't
collide or guess each other's files.

## 2. Why metadata in Postgres, bytes in storage

The file's **bytes** live in MinIO/S3 (cheap, scalable, built for blobs). Its
**metadata** — name, type, size, which message it belongs to, who uploaded it — is an
`Attachment` row in Postgres, so you can query and authorize it. Downloads use a
presigned **GET** URL, so even private files are served securely and directly.

## 3. Full-text search, the right way

`body LIKE '%term%'` can't rank results, ignores word stems, and can't use an index.
Postgres **full-text search** does all three:

```python
vector = SearchVector("body")
query  = SearchQuery(q, search_type="websearch")   # supports "quoted phrases" -minus
qs = (Message.objects
        .annotate(rank=SearchRank(vector, query))
        .filter(rank__gt=0)
        .order_by("-rank"))
```

`websearch` parses Google-style queries; `SearchRank` orders by relevance. Crucially,
search is **scoped to the user's workspaces** first — you can never search channels
you can't see.

## 4. Make it fast: a stored search vector

Computing `SearchVector` on every query re-reads every row. In production you add a
`SearchVectorField` kept up to date (via a trigger or `django.contrib.postgres`'s
tooling) and a **GIN index** on it, so search uses the index instead of a scan. You'll
do this in the challenge.

> Search requires **Postgres** — it won't run on SQLite. This is one place the
> "develop on the real engine" rule from Module 00 pays off.

## 5. Frontend glue

The composer gets an attach button: pick a file → `presign` → `PUT` to storage →
register the attachment → send the message with it. A search box calls
`/api/search/?q=` and renders ranked results that link into their channel. (Built in
the lab/challenge.)

---

## 6. Do the lab

Upload a file end-to-end through MinIO with a presigned URL, attach it to a message,
download it via a presigned GET, then run ranked full-text searches over your history.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

object storage · presigned URL · attachment · full-text search · SearchVector/Rank · GIN index

**Next →** [Module 12: Containerizing the Stack](../12-docker-compose-stack/)
