# Module 04 — Editing with Vim

**Goal:** edit files confidently on any Linux box — including servers where `vim` (or
`vi`) is the only editor installed. ⏱️ ~1 h · 🎯 Prereq: 00–01.

> Why vim? It's **everywhere** (every server, every container, the exams). You don't need
> to be a wizard — you need the **survival subset** so you're never stuck.

---

## 1. Modal editing (the one big idea)

Unlike most editors, vim has **modes**:
- **Normal mode** (the default) — keys are *commands* (move, delete, copy). Press `Esc`
  to return here any time.
- **Insert mode** — keys type text. Enter with `i` (and friends); leave with `Esc`.
- **Command-line mode** — `:` commands like save/quit/search-replace.

> Lost or confused? **Press `Esc`** to get back to Normal mode, then proceed.

## 2. The absolute minimum (save & quit)

```
i          enter Insert mode (type your text)
Esc        back to Normal mode
:w         write (save)
:q         quit
:wq  or ZZ save and quit
:q!        quit WITHOUT saving (discard changes)
:x         save (only if changed) and quit
```
If you "can't get out of vim": `Esc` then `:q!` (discard) or `:wq` (save).

## 3. Moving around (Normal mode)

```
h j k l    left, down, up, right   (arrows also work)
w / b      next / previous word
0 / $      start / end of line
gg / G     top / bottom of file
:42        go to line 42
Ctrl+f / Ctrl+b   page down / up
/word      search forward (n next, N previous)   ?word search backward
```

## 4. Editing (Normal mode)

```
x          delete the character under the cursor
dd         delete (cut) the whole line       3dd  three lines
yy         yank (copy) a line                p    paste after
dw / cw    delete / change a word
r<char>    replace one character
u          undo            Ctrl+r  redo
.          repeat the last change
o / O      open a new line below / above (and enter Insert)
A / I      append at end / insert at start of line
```

## 5. Insert-mode entries

```
i  before cursor   a  after cursor
I  line start      A  line end
o  new line below  O  new line above
```

## 6. Search & replace (command-line)

```
:s/old/new/        replace first on the current line
:s/old/new/g       all on the current line
:%s/old/new/g      all in the whole file
:%s/old/new/gc     ...with confirm (y/n each)
```

## 7. Quality-of-life config

Create `~/.vimrc`:
```vim
syntax on
set number          " line numbers
set expandtab       " spaces instead of tabs
set shiftwidth=2
set tabstop=2
set hlsearch        " highlight search matches
set incsearch       " search as you type
```

## 8. nano — the friendly fallback

If vim isn't your thing for quick edits, **nano** shows its shortcuts on screen:
```bash
nano file
# ^O write out (save), ^X exit, ^W search, ^K cut line, ^U paste   (^ = Ctrl)
```
But learn enough vim to survive — it's the universal default.

---

## Do the lab
Create and edit a config file entirely in vim: navigate, edit, search/replace, save.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
modal editing · Normal/Insert/Command-line mode · `Esc` · `i`/`a`/`o` · `:w`/`:q`/`:wq`/
`:q!` · `dd`/`yy`/`p`/`u` · `/search`/`n` · `:%s/old/new/g` · `~/.vimrc` · nano

**Next →** [Module 05: Users, Groups & Permissions](../05-users-and-permissions/)
