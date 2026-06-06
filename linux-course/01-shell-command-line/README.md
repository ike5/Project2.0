# Module 01 — The Shell & Command Line

**Goal:** drive bash fluently — command structure, getting help, history, and the
keyboard shortcuts that make you fast. ⏱️ ~1.5 h · 🎯 Prereq: 00.

---

## 1. What the shell is

The **shell** (here, **bash**) reads what you type, finds the program, runs it, and shows
the output. Anatomy of a command:
```
 ls   -l  --all   /etc
 │     │    │       │
 cmd  opt  long-opt argument
```
- **Options/flags** modify behavior: short (`-l`), long (`--all`), often combinable (`-la`).
- **Arguments** are what the command acts on (files, dirs, text).
- Commands are **case-sensitive** (`LS` ≠ `ls`), as is everything in Linux.

## 2. Where commands come from: PATH

When you type `ls`, bash searches the directories in **`$PATH`**:
```bash
echo $PATH                 # /usr/local/bin:/usr/bin:/bin:...
which ls                   # /usr/bin/ls  (which file runs)
type cd                    # 'cd is a shell builtin'  (not a file)
type -a python3            # all matches in PATH order
```
Three kinds of "commands": **builtins** (`cd`, `echo`), **binaries** in PATH, and
**aliases**/functions.

## 3. Getting help (your real superpower)

```bash
man ls          # the manual: q quit, /word search, n next, g/G top/bottom
ls --help       # quick usage (most tools)
help cd         # help for shell builtins
apropos copy    # search man page descriptions by keyword
man 5 passwd    # a specific manual *section* (5 = file formats)
```
Man sections worth knowing: **1** user commands, **5** file formats (`/etc/...`),
**8** admin commands.

## 4. Variables & environment

```bash
name="Ada"               # set a shell variable (no spaces around =)
echo "$name"             # use it (quote it!)
export EDITOR=vim        # make it an environment variable (visible to child programs)
env | sort               # all environment variables
echo $HOME $USER $PWD    # common ones
```

## 5. Quoting (matters a lot)

```bash
echo $name               # expands the variable
echo "$name is here"     # double quotes: variables expand
echo '$name is literal'  # single quotes: NOTHING expands
echo "cost is \$5"       # backslash escapes a special char
mkdir "my folder"        # quote names with spaces
```

## 6. Command history

```bash
history                  # numbered list of past commands
!!                       # repeat the last command   (e.g. sudo !!)
!42                      # run command number 42
!ssh                     # last command starting with 'ssh'
!$                       # last argument of the previous command
Ctrl+R                   # reverse-search history (type, Enter to run)
```

## 7. Keyboard shortcuts (speed)

| Keys | Action |
|------|--------|
| `Tab` | autocomplete command/path (press twice to list) |
| `Ctrl+A` / `Ctrl+E` | start / end of line |
| `Ctrl+U` / `Ctrl+K` | delete to start / end |
| `Ctrl+W` | delete previous word |
| `Ctrl+R` | search history |
| `Ctrl+L` | clear screen |
| `Ctrl+C` | cancel current command |
| `Ctrl+D` | end of input / logout |
| `Ctrl+Z` | suspend (then `fg`) |

## 8. Chaining commands

```bash
cmd1; cmd2            # run sequentially (regardless of success)
cmd1 && cmd2         # run cmd2 only if cmd1 SUCCEEDED (exit 0)
cmd1 || cmd2         # run cmd2 only if cmd1 FAILED
cmd1 | cmd2          # pipe cmd1's output into cmd2 (Module 03)
echo $?              # exit status of the last command (0 = success)
```

---

## Do the lab
Explore PATH, help, variables, quoting, history, and chaining hands-on.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
shell · command/option/argument · `PATH` · builtin vs binary · `man`/sections ·
variable/`export`/environment · quoting · history/`!!`/`Ctrl+R` · `&&`/`||`/`;` · `$?`

**Next →** [Module 02: Files & Directories](../02-files-and-directories/)
