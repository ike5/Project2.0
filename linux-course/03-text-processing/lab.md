# Lab 03 — Pipelines on Real Data

**You'll:** redirect streams and build pipelines over system files and a sample web log.
⏱️ ~50 min. Copy [`code/access.log`](./code/access.log) into your VM (or recreate it).

---

## Part A — Streams & redirection
```bash
echo "hello" > out.txt          # create/overwrite
echo "again" >> out.txt         # append
cat out.txt                      # two lines
ls /nope 2> err.txt              # send the error to a file
cat err.txt                      # the error message
ls /etc /nope > all.txt 2>&1     # both streams to one file
grep root /etc/passwd | tee found.txt   # to screen AND file
ls /nope 2>/dev/null || echo "handled" # discard error, react to failure
```

## Part B — Search /etc with grep
```bash
grep -i 'ubuntu' /etc/os-release
grep -c '' /etc/passwd                  # line count (every line "matches" empty)
grep -vE '^\s*(#|$)' /etc/ssh/sshd_config   # active config lines only
grep -rn 'PATH' /etc/profile /etc/profile.d/ 2>/dev/null
```

## Part C — Slice /etc/passwd with cut & awk
```bash
cut -d: -f1 /etc/passwd | head                 # just usernames
awk -F: '{print $1, "->", $7}' /etc/passwd | head    # user -> shell
awk -F: '$3 >= 1000 {print $1}' /etc/passwd          # human users (UID >= 1000)
awk -F: '$7 ~ /nologin|false/ {c++} END{print c+0, "service accounts"}' /etc/passwd
```
✅ You're extracting fields and filtering on them — no scripting yet.

## Part D — Analyze the web log
```bash
cd ~  # wherever access.log is
# Requests per IP, busiest first:
awk '{print $1}' access.log | sort | uniq -c | sort -rn
# Count by HTTP status code (field 9):
awk '{print $9}' access.log | sort | uniq -c | sort -rn
# Only the errors (4xx/5xx):
awk '$9 ~ /^[45]/ {print $1, $9, $7}' access.log
# Total bytes sent (last field):
awk '{sum+=$NF} END{print sum, "bytes"}' access.log
```
✅ Expected highlights: IP `10.0.0.5` is busiest; status `200` most common; the 404/403/500
lines are isolated by the `^[45]` filter.

## Part E — sed transformations
```bash
# Mask the IPs (privacy):
sed -E 's/^[0-9.]+/x.x.x.x/' access.log | head
# Keep only the request line (between the quotes):
sed -E 's/.*"([^"]+)".*/\1/' access.log | head
# Edit a copy in place, with a backup:
cp access.log work.log
sed -i.bak 's/GET/FETCH/g' work.log
diff work.log.bak work.log | head
```

## Part F — Compose a mini report
```bash
{
  echo "=== Top IPs ==="
  awk '{print $1}' access.log | sort | uniq -c | sort -rn
  echo "=== Status codes ==="
  awk '{print $9}' access.log | sort | uniq -c | sort -rn
} | tee report.txt
```
✅ `report.txt` holds a tidy summary built entirely from pipelines.

## What you learned
- Redirect stdout/stderr/stdin; pipe and `tee`; discard with `/dev/null`.
- `grep` (filters, regex, invert), `cut`/`awk` (fields), `sed` (transform/in-place).
- The `sort | uniq -c | sort -rn` frequency idiom and `awk` aggregation.

➡️ **[challenge.md](./challenge.md)** then [Module 04](../04-vim/).
