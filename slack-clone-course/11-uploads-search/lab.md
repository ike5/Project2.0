# Lab 11 — Upload a File, Then Find It

**You'll:** create the storage bucket, upload a file end-to-end via a presigned URL,
attach it to a message, download it with a presigned GET, and run ranked full-text
searches.

⏱️ ~50 min. MinIO + Postgres + the API running. Reuse `$ACCESS`, `$CH`.

---

## Part A — Create the bucket

```bash
python manage.py shell -c "from chat.storage import ensure_bucket; ensure_bucket()"
```
✅ Confirm in the MinIO console (<http://localhost:9001>) that a `slack-uploads`
bucket exists.

---

## Part B — Get a presigned upload URL

```bash
PRESIGN=$(curl -s -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
  -X POST localhost:8000/api/uploads/presign/ \
  -d '{"filename":"notes.txt","content_type":"text/plain"}')
echo "$PRESIGN" | jq
KEY=$(echo "$PRESIGN" | jq -r .key)
URL=$(echo "$PRESIGN" | jq -r .upload_url)
```
✅ Expected: a `key` like `u/<id>/<uuid>/notes.txt` and a long signed `upload_url`.

---

## Part C — Upload the bytes directly to storage

```bash
echo "release checklist: tag, build, deploy" > notes.txt
curl -s -X PUT "$URL" -H 'content-type: text/plain' --upload-file notes.txt -o /dev/null -w "%{http_code}\n"
```
✅ Expected: `200`. The file is now in MinIO — **Django never saw the bytes**. Verify
it appears in the bucket via the MinIO console.

---

## Part D — Register the attachment and post it

```bash
SIZE=$(wc -c < notes.txt)
ATT=$(curl -s -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
  -X POST localhost:8000/api/attachments/ \
  -d "{\"key\":\"$KEY\",\"filename\":\"notes.txt\",\"content_type\":\"text/plain\",\"size\":$SIZE}")
echo "$ATT" | jq
```
✅ Expected: an attachment with a `download_url` (a presigned GET). Fetch it:
```bash
curl -s "$(echo "$ATT" | jq -r .download_url)"
# release checklist: tag, build, deploy
```
✅ **Checkpoint:** you uploaded and downloaded a private file without proxying bytes
through Django.

---

## Part E — Full-text search

Post a few searchable messages, then search:
```bash
for t in "deploy the release tonight" "lunch plans" "release notes are ready"; do
  curl -s -H "Authorization: Bearer $ACCESS" -H 'content-type: application/json' \
    -X POST localhost:8000/api/messages/ -d "{\"channel\":$CH,\"body\":\"$t\"}" >/dev/null
done

curl -s -H "Authorization: Bearer $ACCESS" "localhost:8000/api/search/?q=release" | jq '.results[].body'
```
✅ Expected: the two "release" messages, **ranked** (the more relevant first), and the
"lunch" message excluded. Try a phrase query: `?q=%22release%20notes%22`.

✅ Confirm isolation: a user in a different workspace searching `release` gets nothing
from yours.

---

## What you learned
- Presigned URLs let the browser upload/download directly to storage; Django brokers
  permission only.
- File bytes live in object storage; metadata lives in Postgres.
- Postgres full-text search ranks results and respects workspace scoping.

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 12](../12-docker-compose-stack/).
