# Challenge 11 — Make It Production-Grade

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Validate uploads.** Reject presign requests for disallowed content types or
   oversized files (enforce a max size in the presign response and verify the
   registered `size` matches what's in storage via a HEAD request).

2. **Index the search vector.** Add a `SearchVectorField` to `Message`, keep it
   updated (a Postgres trigger or `django.contrib.postgres`'s `SearchVector` on save),
   and add a `GinIndex`. Show with `EXPLAIN` that search now uses the index.

3. **Search the UI.** Add a search box to the frontend that calls `/api/search/?q=`
   and renders results, each linking to its channel and scrolling to the message.

4. **Thumbnails.** When an image is attached, enqueue a Celery task (Module 07) that
   generates a thumbnail, stores it under a derived key, and saves its key on the
   attachment.

5. **Stretch:** Explain why presigned URLs are safer than making the bucket public or
   proxying downloads through Django — covering expiry, least privilege, and load.

## Success criteria
- [ ] Oversized / wrong-type uploads are rejected.
- [ ] Search uses a GIN-indexed `SearchVectorField` (shown via `EXPLAIN`).
- [ ] The UI can search and jump to results.
- [ ] Image attachments get a generated thumbnail asynchronously.
- [ ] You can justify presigned URLs over public buckets or proxying.
