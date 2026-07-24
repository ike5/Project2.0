# Challenge 03 — Reference Solution

## Task 1: Three-user simulation

```bash
cd ~/git-advanced-course
mkdir challenge03 && cd challenge03
git init --bare remote.git

# Alice
git clone remote.git alice
cd alice
echo "alice's file" > alice.txt && git add alice.txt && git commit -m "alice: add file" && git push origin main
cd ..

# Bob
git clone remote.git bob
cd bob
echo "bob's file" > bob.txt && git add bob.txt && git commit -m "bob: add file" && git push origin main
cd ..

# Charlie
git clone remote.git charlie
cd charlie
echo "charlie's file" > charlie.txt && git add charlie.txt && git commit -m "charlie: add file" && git push origin main
cd ..

# Pull into each
cd alice && git pull origin main && ls
cd ../bob && git pull origin main && ls
cd ../charlie && git pull origin main && ls
cd ..
```

Expected: all three clones contain `alice.txt`, `bob.txt`, and `charlie.txt`.

## Task 2: Conflict resolution

```bash
cd ~/git-advanced-course/challenge03/alice
echo "alice's version of shared" > shared.txt
git add shared.txt && git commit -m "alice: shared.txt" && git push origin main

cd ../bob
echo "bob's version of shared" > shared.txt
git add shared.txt && git commit -m "bob: shared.txt" && git push origin main
# Expected: rejected (non-fast-forward)

git pull origin main
# Expected: CONFLICT in shared.txt

cat shared.txt
# Expected: conflict markers

# Resolve: keep both
echo "alice's version of shared" > shared.txt
echo "bob's version of shared" >> shared.txt

git add shared.txt && git commit -m "merge: resolve shared.txt conflict" && git push origin main
```

## Task 3: Force with lease

```bash
cd ~/git-advanced-course/challenge03/charlie
git fetch origin
git reset --hard HEAD~3  # go back 3 commits
git push --force-with-lease origin main
# Expected: likely fails because remote has commits Charlie hasn't "seen"
# The error message prevents overwriting work Charlie doesn't know about
```

Explanation: `--force-with-lease` checks that the remote ref matches your last
fetch. If Alice or Bob pushed since Charlie's last fetch, the push is rejected.
This prevents Charlie from accidentally erasing their work.

## Task 4: Upstream tracking

```bash
cd ~/git-advanced-course/challenge03/alice
git checkout -b feature-x
echo "feature work" > feature.txt && git add feature.txt && git commit -m "feat: x"
git push -u origin feature-x
git branch -vv
```

Expected:
```
* feature-x  a1b2c3d [origin/feature-x] feat: x
  main       x1y2z3a [origin/main] merge: resolve shared.txt conflict
```

---

## Cleanup

```bash
rm -rf ~/git-advanced-course/challenge03
```
