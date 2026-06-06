# Lab 04 — Survive (and Thrive in) Vim

**You'll:** create and edit a file entirely in vim. ⏱️ ~35 min. In your VM.

> If you ever feel trapped: **`Esc`**, then `:q!` to bail or `:wq` to save.

---

## Part A — Create and write
```bash
vim notes.txt
```
1. Press `i` (Insert mode). Type a few lines:
   ```
   server: web01
   port: 8080
   debug: true
   ```
2. Press `Esc`. Type `:w` and Enter (saved). Type `:q` and Enter (quit).
3. `cat notes.txt` → your three lines. ✅

## Part B — Navigate
```bash
vim notes.txt
```
- `gg` (top), `G` (bottom), `:2` (line 2).
- `0` (line start), `$` (line end), `w`/`b` (word forward/back).
- `/port` then Enter — jumps to "port"; `n` for next match.

## Part C — Edit
- On the `debug: true` line: move there, then `$` to the end. Press `cw`? No — to change
  the word `true`: move onto `t` and press `cw`, type `false`, `Esc`.
- Duplicate a line: put the cursor on `port: 8080`, press `yy` then `p` (pastes a copy below).
- Delete a line: `dd`. Undo it: `u`. Redo: `Ctrl+r`.
- Open a new line below and type: press `o`, type `tls: on`, `Esc`.

✅ Use `u` liberally — undo is your safety net.

## Part D — Search & replace
- Replace every `web01` with `web02` in the file: `:%s/web01/web02/g` Enter.
- With confirmation: `:%s/true/false/gc` then `y`/`n` per match.

## Part E — Save & quit cleanly
- `:wq` (save and quit). Verify:
```bash
cat notes.txt
```
✅ Your edits persisted: `web02`, `false`, the duplicated/added lines.

## Part F — A real edit with sudo
Edit a system file (then discard so you don't change anything):
```bash
sudo vim /etc/hosts
# navigate, look around, then quit WITHOUT saving:
# :q!
```
✅ You can open, inspect, and safely abandon edits to system files — a daily admin task.

## Part G — Make vim nicer
```bash
vim ~/.vimrc
# insert:
#   syntax on
#   set number
#   set hlsearch incsearch
#   set expandtab shiftwidth=2 tabstop=2
# :wq
vim notes.txt    # now with line numbers + syntax + search highlight
```

## What you learned
- Modal editing; entering/leaving Insert mode; `Esc` to recover.
- Navigation (`gg`/`G`/`/search`), editing (`dd`/`yy`/`p`/`cw`/`u`).
- `:%s///g` search-replace; saving/quitting (`:wq`, `:q!`).
- A starter `~/.vimrc`.

➡️ **[challenge.md](./challenge.md)** then [Module 05](../05-users-and-permissions/).
