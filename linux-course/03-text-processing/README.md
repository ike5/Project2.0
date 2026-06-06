# Module 03 — Text Processing & Pipelines

**Goal:** the Unix superpower — compose small tools with pipes to slice, filter, and
transform text (logs, configs, CSVs). ⏱️ ~2.5 h · 🎯 Prereq: 00–02.

> Deep reference: [cheatsheets/regex-and-text.md](../cheatsheets/regex-and-text.md).

---

## 1. The three streams + redirection

Every program has **stdin** (0), **stdout** (1), **stderr** (2).
```bash
cmd > out.txt        # stdout → file (overwrite)
cmd >> out.txt       # stdout → file (append)
cmd 2> err.txt       # stderr → file
cmd > all.txt 2>&1   # both → file (redirect stdout, then point stderr at it)
cmd &> all.txt       # both (bash shorthand)
cmd < in.txt         # file → stdin
cmd1 | cmd2          # cmd1's stdout → cmd2's stdin (a PIPE)
cmd | tee copy.txt   # to a file AND keep flowing downstream
```
`/dev/null` is the "trash" sink: `cmd 2>/dev/null` discards errors.

## 2. Viewing text

```bash
cat f          # whole file       cat -n f   # with line numbers
less f         # pager (q quit, / search, n next, G end)
head -n 20 f   # first 20 lines   tail -n 20 f   # last 20
tail -f log    # follow live (great for logs)
```

## 3. Searching with grep

```bash
grep "error" app.log            # lines containing 'error'
grep -i "error"                 # case-insensitive
grep -rn "TODO" src/            # recursive + line numbers
grep -v "^#"  conf              # lines NOT starting with #
grep -E "warn|error" log        # extended regex (alternation)
grep -o "[0-9]\+" f             # print only the matched part
grep -c "GET" access.log        # count matches
```

## 4. Regular expressions (the pattern language)

| | Meaning |
|---|---------|
| `.` | any char | `^`/`$` | line start/end |
| `*` | 0+ of previous | `[abc]`/`[^abc]` | one of / none |
| `+ ? | () {m,n}` | (ERE: `grep -E`) | escape in BRE: `\+ \? \( \{` |

```bash
grep -E '^[a-z_][a-z0-9_-]*:' /etc/passwd     # lines starting with a username field
grep -Eo '[0-9]{1,3}(\.[0-9]{1,3}){3}' log    # IPv4-ish addresses
```

## 5. Transforming with sed

```bash
sed 's/foo/bar/'         # replace first 'foo' per line
sed 's/foo/bar/g'        # all
sed -E 's/(\w+)@(\w+)/\2:\1/'   # capture groups -> \1 \2
sed -n '10,20p' f        # print lines 10-20 (-n quiet)
sed '/^$/d' f            # delete blank lines
sed -i.bak 's/old/new/g' f      # edit in place, keep f.bak backup
```

## 6. Field processing with awk

`awk` splits each line into fields (`$1`, `$2`, … `$NF` = last; `NF` = count; `NR` = row #).
```bash
awk '{print $1}' access.log                  # first column
awk -F: '{print $1, $6}' /etc/passwd         # user + home dir
awk '$3 >= 1000 {print $1}' f                # condition on a field
awk -F, 'NR>1 {sum+=$2} END{print sum}' data.csv   # skip header, sum col 2
awk '/error/{c++} END{print c+0}' log        # count 'error' lines
```

## 7. The classic toolbox

```bash
cut -d, -f1,3 data.csv       # columns by delimiter
sort | uniq -c | sort -rn    # frequency, most common first (sort BEFORE uniq)
tr 'a-z' 'A-Z'               # translate
tr -s ' '                    # squeeze repeats
wc -l / -w / -c              # count lines/words/bytes
column -t                    # align into columns
xargs                        # turn stdin into command arguments
```

## 8. Putting it together (real examples)

```bash
# Top 5 IPs hitting a web log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head -5

# Users with a login shell (not nologin/false)
grep -vE '(nologin|false)$' /etc/passwd | cut -d: -f1

# Count ERROR vs WARN in a log
grep -oE 'ERROR|WARN' app.log | sort | uniq -c

# Active config lines only (strip comments + blanks)
grep -vE '^\s*(#|$)' /etc/ssh/sshd_config
```

---

## Do the lab
Redirect streams and build pipelines over real system files and a sample log.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Code
[`code/access.log`](./code/access.log) — a small sample web log for the lab.

## Key terms
stdin/stdout/stderr · `>`/`>>`/`2>`/`&>`/`<` · pipe · `tee` · `/dev/null` ·
`grep`/regex (BRE vs ERE) · `sed` (s///, -n, -i) · `awk` (fields/`NR`/`NF`/`END`) ·
`cut`/`sort`/`uniq`/`tr`/`wc`/`xargs`

**Next →** [Module 04: Editing with Vim](../04-vim/)
