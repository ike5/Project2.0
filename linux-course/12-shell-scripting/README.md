# Module 12 — Shell Scripting

**Goal:** turn your command-line skills into robust, reusable bash scripts — variables,
conditionals, loops, functions, arguments, and safety. ⏱️ ~3 h · 🎯 Prereq: 00–11.

---

## 1. Anatomy of a script

```bash
#!/usr/bin/env bash          # shebang: run with bash
set -euo pipefail            # safety (explained below)

name="world"                 # variable (no spaces around =)
echo "Hello, $name"
```
```bash
chmod +x script.sh           # make it executable
./script.sh                  # run it    (or: bash script.sh)
```

## 2. The safety preamble (use it always)

```bash
set -e            # exit immediately if any command fails (non-zero)
set -u            # error on use of an UNSET variable
set -o pipefail   # a pipeline fails if ANY stage fails (not just the last)
# combined: set -euo pipefail
```
This turns silent bugs into loud failures. Add `set -x` while debugging to trace
execution.

## 3. Variables & expansion

```bash
greeting="hi"
echo "$greeting there"            # always quote variables
files=$(ls)                       # command substitution
count=$(( 2 + 3 ))               # arithmetic
echo "${name:-default}"          # use 'default' if name is unset/empty
echo "${name:?must be set}"      # ERROR with message if unset
echo "${path%/}"                 # strip trailing slash
echo "${file##*.}"               # extension (strip up to last dot)
echo "${#greeting}"              # length
```

## 4. Arguments

```bash
echo "$0"        # script name
echo "$1 $2"     # first, second argument
echo "$#"        # number of arguments
echo "$@"        # all arguments (quoted, as separate words)
shift            # drop $1, shifting the rest down
```
```bash
target="${1:?usage: $0 <target>}"   # required arg with a usage message
```

## 5. Conditionals

```bash
if [[ "$x" -gt 10 ]]; then echo big
elif [[ "$x" -eq 10 ]]; then echo ten
else echo small; fi

[[ -f "$f" ]]    # file exists and is a regular file
[[ -d "$d" ]]    # directory exists
[[ -z "$s" ]]    # string is empty;  -n = non-empty
[[ "$a" == "$b" ]]   # string equal;  != not equal
[[ "$n" -lt 5 ]]     # numeric: -lt -le -gt -ge -eq -ne
[[ "$s" == pre* ]]   # glob match
[[ "$s" =~ ^[0-9]+$ ]]   # regex match
```
> Prefer `[[ ... ]]` (bash) over `[ ... ]` (POSIX `test`) — safer with strings and
> supports `=~`, `&&`, `||`.

## 6. Loops

```bash
for f in *.log; do echo "$f"; done
for i in $(seq 1 5); do echo "$i"; done
for ((i=0; i<5; i++)); do echo "$i"; done
while read -r line; do echo "got: $line"; done < file.txt
until ping -c1 host &>/dev/null; do sleep 1; done    # wait for something
```

## 7. case

```bash
case "$1" in
  start)   echo starting ;;
  stop)    echo stopping ;;
  restart) echo restarting ;;
  *)       echo "usage: $0 {start|stop|restart}"; exit 1 ;;
esac
```

## 8. Functions

```bash
log() { echo "[$(date +%T)] $*"; }       # $* = all args
add() { echo $(( $1 + $2 )); }
result=$(add 3 4)                          # capture output
log "result is $result"
```

## 9. Exit codes & error handling

```bash
command || { echo "failed" >&2; exit 1; }     # handle failure
trap 'echo "cleaning up"; rm -f "$tmp"' EXIT   # run on exit (any reason)
tmp=$(mktemp)
[[ $? -eq 0 ]]                                  # $? = last exit status
exit 0                                          # explicit success
```

## 10. Reading input & here-docs

```bash
read -rp "Continue? [y/N] " ans
[[ "$ans" == [yY] ]] || exit 0

cat > config.txt <<EOF      # here-doc (variables expand)
host=$HOSTNAME
port=8080
EOF
```

---

## Do the lab
Write and harden a real script that audits a directory and a service. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
[`code/sysreport.sh`](./code/sysreport.sh) — a worked example you'll study and extend.

## Key terms
shebang · `set -euo pipefail` · quoting/expansion (`${var:-}`, `${var:?}`, `${v##*.}`) ·
`$1`/`$@`/`$#`/`shift` · `[[ ]]` tests · `for`/`while`/`until`/`case` · functions ·
exit codes/`$?`/`trap` · `read`/here-doc · `set -x` debugging

**Next →** [Module 13: SSH & Remote Access](../13-ssh-remote-access/)
