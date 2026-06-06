# Challenge 05 — Permissions Puzzles

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Octal ↔ symbolic.** Convert: (a) `rwxr-x---` to octal, (b) `0644` to symbolic,
   (c) the `chmod` symbolic command to take `0664` and remove all "other" access.

2. **Why can't they read it?** A file is `-rw-r--r-- root root secret.txt` inside
   `/srv/data` which is `drwx------ root root`. User `bob` is in no special group. Can bob
   read `secret.txt`? Explain using the directory-traversal rule, and give the minimal
   change to let bob read it.

3. **Build a dropbox.** Create `/srv/incoming` where anyone can **add** files but only the
   file's owner (and root) can delete or read others' files is *not* required — just:
   anyone may create files, nobody may delete someone else's. Which bit do you need?

4. **Shared project dir.** Set up `/srv/project` owned by group `eng` such that: members
   can create/edit, new files are automatically group `eng`, and others have no access.
   Give the exact `chown`/`chmod`.

5. **Audit.** Write the `find` command to list every setuid binary on the system, and
   explain why setuid root binaries are a security concern.

## Success criteria
- [ ] Correct octal/symbolic conversions.
- [ ] Correct reasoning that bob **cannot** traverse `drwx------`, plus the fix.
- [ ] Sticky bit identified for the dropbox.
- [ ] `chown root:eng` + `chmod 2770` for the project dir.
- [ ] Correct setuid `find` and a sound security explanation.
