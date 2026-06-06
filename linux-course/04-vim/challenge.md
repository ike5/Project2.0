# Challenge 04 — Vim Without Looking

Solutions in [`solutions/`](./solutions/). Do these from memory where you can.

## Tasks
1. **Speed run.** Create `app.conf` in vim with 5 lines of `key = value`. Save and quit
   with `ZZ` (not `:wq`).

2. **Targeted edits.** Reopen it and, using Normal-mode commands only (no mouse):
   delete line 3 (`dd`), copy line 1 to the bottom (`yy`, `G`, `p`), and change the first
   `value` to `enabled` (`cw`).

3. **Global replace.** Replace every `=` with ` : ` throughout the file in one command.

4. **Bail out.** Make a mess of the file, then exit **without saving** so the file is
   unchanged on disk. Verify with `cat`.

5. **Quiz (write the keystrokes):**
   - Go to line 20.
   - Search for "error" and jump to the 3rd occurrence.
   - Undo your last 3 changes.
   - Insert text at the very end of the current line.

## Success criteria
- [ ] File created/saved with `ZZ`.
- [ ] Line deleted, line 1 duplicated at the bottom, a word changed — all in Normal mode.
- [ ] `:%s/=/ : /g` performed.
- [ ] You discarded changes with `:q!` and confirmed the file is unchanged.
- [ ] Correct keystrokes for the quiz.
