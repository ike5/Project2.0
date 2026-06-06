# Regex & Text Processing Cheatsheet

## Regular expressions (POSIX, as used by grep/sed/awk)

| Pattern | Matches |
|---------|---------|
| `.` | any single character |
| `^` / `$` | start / end of line |
| `*` | zero or more of the previous |
| `[abc]` / `[^abc]` | one of / none of |
| `[a-z]` `[0-9]` | ranges |
| `\<` `\>` | word boundaries (GNU) |
| **ERE** (`grep -E`, `sed -E`, awk) | `+` `?` `|` `(...)` `{m,n}` work unescaped |
| **BRE** (default grep/sed) | escape them: `\+` `\?` `\(` `\{` |

Handy character classes: `[[:digit:]]`, `[[:alpha:]]`, `[[:space:]]`, `[[:alnum:]]`.

## grep — search
```bash
grep "pat" file              # lines matching
grep -i "pat"                # case-insensitive
grep -r "pat" dir/           # recursive
grep -n "pat"                # show line numbers
grep -v "pat"                # invert (non-matching)
grep -c "pat"                # count
grep -E "foo|bar"            # extended regex (alternation)
grep -o "[0-9]+"             # print only the match
grep -A2 -B2 "pat"           # 2 lines after/before context
grep -l "pat" *.conf         # just filenames that match
```

## sed — stream edit
```bash
sed 's/old/new/'             # replace first per line
sed 's/old/new/g'            # replace all
sed -E 's/([0-9]+)/<\1>/g'   # backreference \1 to a capture group
sed -n '2,5p' file           # print only lines 2-5 (-n = quiet)
sed '/^#/d' file             # delete comment lines
sed -i 's/foo/bar/g' file    # edit in place (use -i.bak to back up)
sed '3a\appended text'       # append after line 3
```

## awk — fields & logic
```bash
awk '{print $1, $3}'                 # columns 1 and 3 (whitespace-split)
awk -F: '{print $1}' /etc/passwd     # custom field separator
awk '$3 > 1000 {print $1}' f         # condition on a numeric field
awk '/error/{c++} END{print c}'      # count matches
awk 'NR==1{next} {sum+=$2} END{print sum}'   # skip header, sum column 2
awk -F, 'BEGIN{OFS="\t"} {print $2,$1}'      # reorder CSV -> TSV
```

## Cut, sort, uniq, and friends
```bash
cut -d: -f1,7 /etc/passwd     # fields by delimiter
cut -c1-10 file               # characters
sort file;  sort -n;  sort -r;  sort -k2,2 -t,    # numeric/reverse/by-key
uniq;  uniq -c;  uniq -d      # adjacent dups (sort first!)
sort file | uniq -c | sort -rn | head    # top-N frequency
tr 'a-z' 'A-Z';  tr -d ' ';  tr -s ' '   # translate / delete / squeeze
wc -l -w -c file              # lines / words / bytes
paste a b;  join a b          # merge files by line / key
column -t                     # align columns for reading
```

## Redirection & pipes recap
```bash
cmd > out         # stdout to file (overwrite)
cmd >> out        # append
cmd 2> err        # stderr to file
cmd > out 2>&1    # both to file (order matters)
cmd &> out        # both (bash shorthand)
cmd1 | cmd2       # pipe stdout to next stdin
cmd | tee file    # to file AND onward
cmd < input       # file as stdin
cmd <<'EOF' ...   # here-doc (literal with quotes)
```

## Common one-liners
```bash
# Top 10 IPs in an access log
awk '{print $1}' access.log | sort | uniq -c | sort -rn | head

# Extract all email-ish strings
grep -Eo '[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}' file

# Replace tabs with commas
sed 's/\t/,/g' file

# Sum a column of numbers
awk '{s+=$1} END{print s}' file

# Show non-comment, non-blank config lines
grep -vE '^\s*(#|$)' /etc/ssh/sshd_config
```
