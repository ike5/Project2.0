# Lab 01 — Drive the Shell

**You'll:** practice PATH, help, variables, quoting, history, and chaining. ⏱️ ~35 min.
Run everything inside your `lab` VM (`multipass shell lab`).

---

## Part A — Who/where am I
```bash
whoami; id; hostname; pwd
echo "Shell is $SHELL, home is $HOME"
```
✅ You see your user, groups, host, current dir, and shell.

## Part B — PATH & command types
```bash
echo $PATH
which ls; which cd; type cd; type ls; type -a ls
```
✅ Note `cd` is a **builtin** (no path), `ls` is a **binary** at `/usr/bin/ls`.
Add a directory to PATH for this session:
```bash
mkdir -p ~/bin
export PATH="$HOME/bin:$PATH"
echo $PATH        # ~/bin is now first
```

## Part C — Help systems
```bash
man ls            # scroll with arrows; /human then Enter to find '-h'; q to quit
ls --help | head
apropos directory | head
man 5 passwd | head -20      # the FILE FORMAT of /etc/passwd (section 5)
```
✅ You can find what a flag does without leaving the terminal.

## Part D — Variables & quoting
```bash
greeting="hello world"
echo $greeting            # hello world
echo "$greeting"          # hello world  (safe)
echo '$greeting'          # $greeting    (literal)
files=*.txt
echo "$files"             # *.txt        (quoted: not expanded)
echo $files               # expands to matching files (or *.txt if none)
export GREETING="$greeting"
bash -c 'echo "child sees: $GREETING"'    # exported -> visible to child shell
```
✅ Understand when `$var` expands and when globbing happens.

## Part E — History & shortcuts
```bash
ls /etc >/dev/null
pwd
history | tail -5
!!                 # re-runs pwd
echo done; !pwd    # runs the last 'pwd' command
# Now press Ctrl+R, type 'ls /etc', press Enter.
```
Try the editing shortcuts: type a long line, then `Ctrl+A`, `Ctrl+E`, `Ctrl+W`, `Ctrl+U`.

## Part F — Chaining & exit status
```bash
true;  echo "exit: $?"        # 0
false; echo "exit: $?"        # 1
mkdir -p /tmp/demo && cd /tmp/demo && pwd     # each step gates the next
ls /nope || echo "that failed, as expected"
cat /etc/hostname; echo "status $?"
```
✅ `&&` stops on failure; `||` reacts to failure; `$?` reports the last status.

## Part G — Make an alias (and a lasting one)
```bash
alias ll='ls -lah'
ll
# Persist it for future shells:
echo "alias ll='ls -lah'" >> ~/.bashrc
source ~/.bashrc        # reload current shell
```
✅ `ll` works now and in future sessions (it's in your `~/.bashrc`).

## What you learned
- Command structure, PATH, builtins vs binaries.
- `man`/`--help`/`apropos` to self-serve.
- Variable expansion, quoting rules, and globbing.
- History tricks, editing shortcuts, `&&`/`||`/`;`, `$?`, and aliases.

➡️ **[challenge.md](./challenge.md)** then [Module 02](../02-files-and-directories/).
