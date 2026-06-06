# Lab 12 — Write Real Scripts

**You'll:** run and dissect a worked script, then write your own with safety, arguments,
loops, and functions. ⏱️ ~60 min. In your VM.

---

## Part A — Run the worked example
```bash
install -m 0755 code/sysreport.sh /usr/local/bin/sysreport.sh
sysreport.sh                      # default: checks ssh, cron
sysreport.sh -v nginx ssh         # verbose, custom services
sudo sysreport.sh                 # the auth-failures section now works
```
✅ A tidy, sectioned report. Open `code/sysreport.sh` and match each part to the README:
`set -euo pipefail`, `getopts`, the `services` array + default, `log`/`vlog` functions,
the `for` loop, and the conditional log read.

## Part B — Safety preamble in action
Create `unsafe.sh`:
```bash
#!/usr/bin/env bash
echo "value is $UNDEFINED_VAR"
rm -rf "$EMPTY/important"        # if EMPTY is unset, this is catastrophic
echo "still here"
```
Run it, then add `set -euo pipefail` at the top and run again:
```bash
bash unsafe.sh                    # silently uses empty vars (dangerous)
sed -i '1a set -euo pipefail' unsafe.sh
bash unsafe.sh                    # now ERRORS on $UNDEFINED_VAR before any damage
```
✅ `set -u` caught the unset variable before the dangerous `rm`. This is why every script
should start with the preamble.

## Part C — Arguments & usage
Create `greet.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
name="${1:?usage: $0 <name> [greeting]}"
greeting="${2:-Hello}"
echo "$greeting, $name!"
```
```bash
chmod +x greet.sh
./greet.sh                  # prints usage and exits non-zero
./greet.sh Ada              # Hello, Ada!
./greet.sh Ada Hi           # Hi, Ada!
echo "exit: $?"
```

## Part D — Loops & conditionals
Create `checkfiles.sh` that reports each `.conf` under `/etc/ssh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
dir="${1:-/etc/ssh}"
count=0
for f in "$dir"/*; do
  [[ -f "$f" ]] || continue
  size=$(stat -c%s "$f")
  if [[ "$size" -gt 1000 ]]; then tag="(large)"; else tag=""; fi
  printf "%-40s %6d bytes %s\n" "$f" "$size" "$tag"
  count=$(( count + 1 ))
done
echo "checked $count files"
```
```bash
chmod +x checkfiles.sh; ./checkfiles.sh
```

## Part E — Functions, trap, and a temp file
Create `withtmp.sh`:
```bash
#!/usr/bin/env bash
set -euo pipefail
tmp=$(mktemp)
trap 'rm -f "$tmp"; echo "cleaned up $tmp"' EXIT     # runs no matter how we exit

fill() { seq 1 "$1" > "$tmp"; }
fill 5
echo "tmp has $(wc -l < "$tmp") lines"
# exit (trap fires and removes the temp file)
```
```bash
bash withtmp.sh
```
✅ The `trap ... EXIT` cleaned up the temp file even though we never `rm`'d it explicitly.

## Part F — Debugging
```bash
bash -x greet.sh Ada Hi          # trace every expansion/command
# or add 'set -x' inside a script to trace a section.
```

## What you learned
- The safety preamble (`set -euo pipefail`) and why it matters.
- Arguments/usage (`${1:?}`, `${2:-}`), `getopts`, arrays.
- Loops, `[[ ]]` tests, functions, `trap ... EXIT`, and `-x` debugging.

➡️ **[challenge.md](./challenge.md)** then [Module 13](../13-ssh-remote-access/).
