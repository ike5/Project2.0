# Lab 03 — Simulate a Multi-User Remote

**You'll:** create a bare remote, simulate two users pulling and pushing,
handle non-fast-forward errors, and practice force-with-lease. ⏱️ ~40 min.

We'll use a **bare repository** as a "remote" — no working tree, just the
`.git` data. This simulates GitHub without needing internet access.

## Part A — Create a bare remote

```bash
cd ~/git-advanced-course
mkdir lab03 && cd lab03
git init --bare remote.git
```

Expected:
```
Initialized empty Git repository in /Users/you/git-advanced-course/lab03/remote.git/
```

## Part B — Clone as user A

```bash
git clone remote.git userA
cd userA
echo "user A's first file" > a.txt
git add a.txt
git commit -m "user A: initial commit"
git push origin main
```

Expected:
```
Enumerating objects: 4, done.
...
To /Users/you/git-advanced-course/lab03/remote.git
 * [new branch]      main -> main
```

✅ Check: `git log --oneline` shows the commit.

## Part C — Clone as user B

```bash
cd ~/git-advanced-course/lab03
git clone remote.git userB
cd userB
git log --oneline
```

Expected:
```
a1b2c3d user A: initial commit
```

✅ Check: userB sees userA's commit.

## Part D — User B pushes a change

```bash
cd ~/git-advanced-course/lab03/userB
echo "user B's work" > b.txt
git add b.txt
git commit -m "user B: add b.txt"
git push origin main
```

Expected: push succeeds.

## Part E — User A pulls (fast-forward)

```bash
cd ~/git-advanced-course/lab03/userA
git pull origin main
```

Expected:
```
remote: Enumerating objects: 4, done.
...
Fast-forward
 b.txt | 1 +
 1 file changed, 1 insertion(+)
 create mode 100644 b.txt
```

✅ Check: `cat b.txt` shows "user B's work".

## Part F — Create a non-fast-forward situation

User A makes a local commit:

```bash
cd ~/git-advanced-course/lab03/userA
echo "user A's new work" > c.txt
git add c.txt
git commit -m "user A: add c.txt"
```

User B also makes a commit on the same branch:

```bash
cd ~/git-advanced-course/lab03/userB
echo "user B's other work" > d.txt
git add d.txt
git commit -m "user B: add d.txt"
git push origin main
```

Now user A tries to push:

```bash
cd ~/git-advanced-course/lab03/userA
git push origin main
```

Expected error:
```
! [rejected]        main -> main (non-fast-forward)
error: failed to push some refs
hint: Updates were rejected because the tip of your current branch is behind
hint: its remote counterpart.
```

✅ Check: the push fails with "non-fast-forward".

## Part G — Pull and resolve (merge)

```bash
cd ~/git-advanced-course/lab03/userA
git pull origin main
```

Expected: Git merges the remote changes with your local commit.

```bash
git log --oneline
```

Expected: a merge commit appears.

```bash
git push origin main
```

Expected: push succeeds now.

## Part H — Force with lease scenario

Reset userA's local to simulate a divergence:

```bash
cd ~/git-advanced-course/lab03/userA
git log --oneline
# Note the hash of the second-to-last commit
git reset --hard HEAD~1
git push --force-with-lease origin main
```

Expected: either succeeds (if remote hasn't changed) or fails with a warning
(protecting against overwriting unseen changes).

If it fails, the output will look like:
```
! [rejected]        main -> main (lease was declined)
```

This is the safety mechanism — it prevents you from overwriting work you
haven't seen.

## Part I — Inspect upstream tracking

```bash
cd ~/git-advanced-course/lab03/userA
git branch -vv
```

Expected:
```
* main  x1y2z3 [origin/main] user A: latest
```

The `[origin/main]` shows the upstream tracking.

## Part J — Clean up

```bash
rm -rf ~/git-advanced-course/lab03
```

✅ Check: the directory no longer exists.

---

**Next →** [Challenge 03](./challenge.md)
