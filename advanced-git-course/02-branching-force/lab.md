# Lab 02 — Break Things and Recover

**You'll:** force checkout over dirty work, use all three reset modes, recover
from reflog, rebase a feature branch, and cherry-pick a commit. ⏱️ ~50 min.

## Part A — Force checkout over dirty changes

```bash
cd ~/git-advanced-course
mkdir lab02 && cd lab02
git init
echo "version 1" > file.txt
git add file.txt
git commit -m "version 1"
```

Expected:
```
[main a1b2c3d] version 1
 1 file changed, 1 insertion(+)
 create mode 100644 file.txt
```

Now create a branch and make changes:

```bash
git checkout -b feature
echo "version 2" > file.txt
echo "new file" > new.txt
git add file.txt
```

We have `file.txt` staged and `new.txt` untracked. Now force checkout:

```bash
git checkout -f main
```

Expected: no error, clean switch to main.

```bash
cat file.txt
git status
```

Expected:
```
version 1
nothing to commit, working tree clean
```

✅ Check: `file.txt` is back to "version 1", `new.txt` is gone, no uncommitted
changes.

## Part B — Soft reset

```bash
cd ~/git-advanced-course/lab02
git checkout -b experiment
echo "change 1" > a.txt
git add a.txt
git commit -m "commit A"
echo "change 2" > b.txt
git add b.txt
git commit -m "commit B"
echo "change 3" > c.txt
git add c.txt
git commit -m "commit C"
git log --oneline
```

Expected:
```
d4e5f6g commit C
a1b2c3d commit B
e4f5g6h commit A
i7j8k9l version 1
```

Soft reset — undo commit C but keep changes staged:

```bash
git reset --soft HEAD~1
git log --oneline
git status
```

Expected:
```
a1b2c3d commit B
e4f5g6h commit A
i7j8k9l version 1

Changes to be committed:
  new file:   c.txt
```

✅ Check: commit C is gone, but `c.txt` is still staged.

## Part C — Mixed reset

```bash
cd ~/git-advanced-course/lab02
git reset --mixed HEAD~1
git log --oneline
git status
```

Expected:
```
e4f5g6h commit A
i7j8k9l version 1

Changes not staged for commit:
  new file:   c.txt
```

✅ Check: commit B is gone, `c.txt` is modified but unstaged.

## Part D — Hard reset and reflog recovery

```bash
cd ~/git-advanced-course/lab02
git reset --hard e4f5g6h
git log --oneline
git status
```

Expected:
```
e4f5g6h commit A
i7j8k9l version 1

nothing to commit, working tree clean
```

Commit B and C are "gone." Now recover with reflog:

```bash
git reflog
```

Expected output (hashes will differ):
```
e4f5g6h HEAD@{0}: reset: moving to e4f5g6h
a1b2c3d HEAD@{1}: reset: mixed: moving to HEAD~1
d4e5f6g HEAD@{2}: commit: commit C
a1b2c3d HEAD@{3}: commit: commit B
e4f5g6h HEAD@{4}: commit: commit A
...
```

Find the hash for commit C (the one before the reset). Then recover:

```bash
git reset --hard d4e5f6g
git log --oneline
```

Expected:
```
d4e5f6g commit C
a1b2c3d commit B
e4f5g6h commit A
i7j8k9l version 1
```

✅ Check: all three commits are back.

## Part E — Rebase

```bash
cd ~/git-advanced-course/lab02
git checkout main
echo "main line 1" >> main.txt
git add main.txt
git commit -m "main line 1"
```

Expected:
```
[main x1y2z3] main line 1
```

```bash
git checkout -b feature-rebase
echo "feature work" > feature.txt
git add feature.txt
git commit -m "feature work"
git log --oneline --graph
```

Expected:
```
* c1d2e3f (feature-rebase) feature work
* x1y2z3 (HEAD -> main) main line 1
* i7j8k9l version 1
```

Now rebase onto main:

```bash
git rebase main
git log --oneline --graph
```

Expected:
```
* f1g2h3i (feature-rebase) feature work
* x1y2z3 (main) main line 1
* i7j8k9l version 1
```

✅ Check: feature work is now on top of main. The history is linear.

## Part F — Cherry-pick

```bash
cd ~/git-advanced-course/lab02
git checkout main
echo "bugfix" > bugfix.txt
git add bugfix.txt
git commit -m "fix: important bugfix on main"
git log --oneline
```

Expected:
```
j1k2l3m fix: important bugfix on main
x1y2z3 main line 1
i7j8k9l version 1
```

```bash
git checkout feature-rebase
git cherry-pick j1k2l3m
git log --oneline
```

Expected:
```
m1n2o3p (feature-rebase) fix: important bugfix on main
f1g2h3i feature work
x1y2z3 (main) main line 1
i7j8k9l version 1
```

✅ Check: the bugfix commit appears on `feature-rebase` with a new hash.

## Part G — Clean up

```bash
rm -rf ~/git-advanced-course/lab02
```

✅ Check: the directory no longer exists.

---

**Next →** [Challenge 02](./challenge.md)
