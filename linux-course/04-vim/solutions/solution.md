# Challenge 04 — Reference Solution

### 1. Speed run
```
vim app.conf
i
key1 = value
key2 = value
key3 = value
key4 = value
key5 = value
Esc
ZZ              (save and quit — same as :wq)
```

### 2. Targeted edits (Normal mode)
```
vim app.conf
:3        (or 3G) then  dd        # delete line 3
gg                                # line 1
yy                                # yank it
G                                 # last line
p                                 # paste the copy below
gg                                # back to line 1
f v  (or w w)  then  cw  enabled  Esc   # change the first 'value' -> 'enabled'
:wq
```

### 3. Global replace
```
:%s/=/ : /g
```

### 4. Bail out
```
vim app.conf
(make random edits: dd, x, i garbage Esc ...)
:q!                  # quit, discard everything
cat app.conf         # unchanged from the last save
```

### 5. Quiz keystrokes
- Go to line 20: `:20` (or `20G`).
- Search "error", 3rd occurrence: `/error` Enter, then `n` `n` (next, next).
- Undo last 3 changes: `u` `u` `u` (or `3u`).
- Insert at end of current line: `A`.
