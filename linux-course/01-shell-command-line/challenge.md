# Challenge 01 — Shell Fluency

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Self-serve help.** Without searching the web, use `man`/`--help` to find: the `ls`
   flag that sorts by modification time, and the one that appends a `/` to directories.
   Show the command you'd use to list `/etc` newest-first with type indicators.

2. **PATH detective.** Determine which `python3` runs, every `python3` in your PATH, and
   whether `ll` is a builtin, alias, or binary. State the command for each answer.

3. **Quoting puzzle.** Predict the output of each, then verify:
   ```bash
   x="a b"
   echo $x        # ?
   echo "$x"      # ?
   echo '$x'      # ?
   touch "$x"; ls # how many files?
   ```

4. **Conditional chain.** Write a one-liner that creates `/tmp/proj/logs` (including
   parents), and **only if that succeeds**, prints "ready", otherwise prints "failed".

5. **History recall.** Using only history expansion (no retyping), re-run the last
   command that started with `man`, and separately reuse the last argument of your
   previous command in a new `ls` command.

## Success criteria
- [ ] Correct `ls` flags found via help (`-t`, `-F`), combined for the listing.
- [ ] You identified the python path, all matches, and `ll`'s type.
- [ ] Quoting outputs predicted correctly; `touch "$x"` makes **one** file `a b`.
- [ ] The `mkdir -p ... && echo ready || echo failed` one-liner works.
- [ ] You used `!man` and `!$` instead of retyping.
