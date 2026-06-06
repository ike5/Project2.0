# Challenge 02 — Files & Find

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **One-command tree.** With a single `mkdir` and a single `touch` (using brace
   expansion), create `site/{html,css,js}` containing `index.html`, `style.css`, and
   `app.js` respectively. Show your two commands.

2. **Link behavior.** Create a file `data.txt`, a hard link `h.txt`, and a symlink
   `s.txt` to it. Then `mv data.txt data2.txt`. Which of `h.txt` / `s.txt` still works,
   and why? Verify with `cat` and `ls -li`.

3. **Find the big, old logs.** In `/var/log`, list all `*.log` files larger than 1 MB OR
   not modified in the last 7 days. (Hint: two `find` runs, or `-o` with grouping.)

4. **Safe cleanup.** Write a command that finds all `*.tmp` files under your home dir and
   shows them, then a second command that deletes them — explaining why you'd run the
   "show" version first.

5. **Stretch:** Explain why `rm -rf "$DIR/"` is dangerous if `$DIR` is unset, and one
   habit that prevents the disaster.

## Success criteria
- [ ] Two-command tree built with brace expansion.
- [ ] After the move: the **hard** link works, the **symlink** breaks; you can explain why.
- [ ] Correct `find` for large-or-old logs.
- [ ] Show-then-delete workflow articulated.
