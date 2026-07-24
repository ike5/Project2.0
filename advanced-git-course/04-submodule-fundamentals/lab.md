# Lab 04 — Create and Manage Submodules

**You'll:** create two "library" repos, add them as submodules to a parent repo,
inspect `.gitmodules`, clone a fresh copy, and update submodules. ⏱️ ~60 min.

## Part A — Create the parent repo

```bash
cd ~/git-advanced-course
mkdir lab04 && cd lab04
git init parent-repo
cd parent-repo
echo "# Parent Project" > README.md
git add README.md
git commit -m "initial commit"
```

Expected:
```
[main a1b2c3d] initial commit
 1 file changed, 1 insertion(+)
 create mode 100644 README.md
```

✅ Check: `git log --oneline` shows one commit.

## Part B — Create two "library" repos

We'll create bare repos to simulate remote libraries:

```bash
cd ~/git-advanced-course/lab04
git init --bare library-a.git
git init --bare library-b.git
```

Clone each and add content:

```bash
git clone library-a.git lib-a-work
cd lib-a-work
echo "Library A: utility functions" > utils.sh
git add utils.sh
git commit -m "initial: utility functions"
git push origin main
cd ..

git clone library-b.git lib-b-work
cd lib-b-work
echo "Library B: config parser" > parser.py
git add parser.py
git commit -m "initial: config parser"
git push origin main
cd ..
```

✅ Check: both libraries have content and are pushed to their bare remotes.

## Part C — Add submodules to the parent

```bash
cd ~/git-advanced-course/lab04/parent-repo
git submodule add ../library-a.git libs/library-a
git submodule add ../library-b.git libs/library-b
```

Expected:
```
Cloning into '/Users/you/git-advanced-course/lab04/parent-repo/libs/library-a'...
Cloning into '/Users/you/git-advanced-course/lab04/parent-repo/libs/library-b'...
```

Check the result:

```bash
cat .gitmodules
```

Expected:
```
[submodule "libs/library-a"]
    path = libs/library-a
    url = ../library-a.git
[submodule "libs/library-b"]
    path = libs/library-b
    url = ../library-b.git
```

```bash
git status
```

Expected:
```
Changes to be committed:
  new file:   .gitmodules
  new file:   libs/library-a
  new file:   libs/library-b
```

✅ Check: `.gitmodules` exists and lists both submodules.

## Part D — Commit the parent

```bash
git add .gitmodules
git commit -m "add submodules library-a and library-b"
```

Expected:
```
[main b2c3d4e] add submodules library-a and library-b
 3 files changed, 8 insertions(+)
 create mode 100644 .gitmodules
 create mode 100644 libs/library-a
 create mode 100644 libs/library-b
```

✅ Check: `git log --oneline` shows two commits.

## Part E — Inspect submodule content

```bash
ls libs/library-a/
cat libs/library-a/utils.sh
```

Expected:
```
Library A: utility functions
```

```bash
ls libs/library-b/
cat libs/library-b/parser.py
```

Expected:
```
Library B: config parser
```

✅ Check: both submodule directories contain their library files.

## Part F — Check submodule status

```bash
git submodule status
```

Expected:
```
 a1b2c3d libs/library-a (heads/main)
 b2c3d4e libs/library-b (heads/main)
```

The leading space means both are at the expected commit.

## Part G — Simulate a fresh clone

```bash
cd ~/git-advanced-course/lab04
git clone parent-repo fresh-clone
ls fresh-clone/libs/library-a/
```

Expected: empty directory. The submodule files are NOT there.

```bash
git -C fresh-clone submodule status
```

Expected:
```
-a1b2c3d libs/library-a (heads/main)
-b2c3d4e libs/library-b (heads/main)
```

The `-` prefix means "not initialized."

## Part H — Initialize and update submodules

```bash
git -C fresh-clone submodule update --init --recursive
ls fresh-clone/libs/library-a/
```

Expected: `utils.sh` is now present.

```bash
git -C fresh-clone submodule status
```

Expected:
```
 a1b2c3d libs/library-a (heads/main)
 b2c3d4e libs/library-b (heads/main)
```

✅ Check: submodule files are present and status shows no prefix (clean).

## Part I — One-step clone with --recurse-submodules

```bash
cd ~/git-advanced-course/lab04
git clone --recurse-submodules parent-repo one-step-clone
ls one-step-clone/libs/library-a/
ls one-step-clone/libs/library-b/
```

Expected: both contain their files immediately.

✅ Check: no separate `submodule update` needed.

## Part J — Clean up

```bash
rm -rf ~/git-advanced-course/lab04
```

✅ Check: the directory no longer exists.

---

**Next →** [Challenge 04](./challenge.md)
