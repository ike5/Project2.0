# Linux Administration: From the Command Line to Mastery 🐧

A hands-on course that takes you through **Linux fundamentals and administration** —
everything you'd see on the **LPIC-1 / CompTIA Linux+** exams, and more — by actually
doing the work on a real Linux system.

> **Who this is for:** You're comfortable enough to open a terminal and want real,
> practical Linux administration skills. No prior Linux admin experience assumed. This is
> part of a series (Kubernetes, .NET, Swift/iOS), and it pairs naturally with the
> Kubernetes course.
>
> **Next step:** once you can administer Linux by hand, the separate
> **[Ansible course](../ansible-course/)** teaches you to automate all of this work as
> code — that's the natural sequel.

---

## The arc

```
  Fundamentals                      Administration
 ┌───────────────┐                ┌──────────────────────────────┐
 │ shell, files, │ ─────────────▶ │ systemd, storage, networking,│
 │ text, perms,  │                │ scheduling, scripting, ssh,  │
 │ processes,    │                │ security, containers         │
 │ packages      │                └──────────────────────────────┘
 └───────────────┘                       ▼
                              then automate it all in the
                              separate ▶ Ansible course
```

---

## What makes it effective

- **Learn by doing.** Every module = concise concepts + a guided lab on a real Linux box
  + an unguided challenge + reference solutions.
- **Exam-aligned, not exam-trapped.** Covers the LPIC-1 (101/102) and Linux+ topic areas,
  but focuses on doing the work, with **distro call-outs** for both the Debian/Ubuntu
  (`apt`) and RHEL/Fedora (`dnf`) families that the exams test.
- **A capstone.** Build and harden a small real service (a web server behind a firewall,
  with users, storage, logging, and a backup) end to end — by hand.
- **Sets up automation.** Everything you do here is exactly what the separate
  **[Ansible course](../ansible-course/)** later teaches you to codify.

---

## Prerequisites

- A computer that can run a Linux VM. On a **Mac**, we use **Multipass** (free, quick
  Ubuntu VMs); Docker containers are used for some quick labs and the multi-host Ansible
  work. (Windows users can use WSL2 or a VM; the commands are identical.)
- Willingness to live in a terminal.

Primary distro for labs: **Ubuntu LTS** (`apt`, `systemd`). Throughout, **"RHEL family"**
boxes show the `dnf`/`rpm`/`firewalld` equivalents so you're ready for either.

---

## The learning path

### Phase 0 — Setup
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 00 | [Setup & Orientation](./00-setup/) | Spin up a Linux VM on your Mac; orient in the shell | 45 min |

### Phase 1 — Linux Fundamentals (LPIC-1 101)
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 01 | [The Shell & Command Line](./01-shell-command-line/) | Drive bash: commands, help, history, shortcuts | 1.5 h |
| 02 | [Files & Directories](./02-files-and-directories/) | Navigate the FHS; manage files; links; globbing | 2 h |
| 03 | [Text Processing & Pipelines](./03-text-processing/) | Redirection, pipes, grep/sed/awk, regex | 2.5 h |
| 04 | [Editing with Vim](./04-vim/) | Edit files anywhere with the survival subset of vim | 1 h |
| 05 | [Users, Groups & Permissions](./05-users-and-permissions/) | Manage accounts; `chmod`/`chown`; sudo; special bits | 2.5 h |
| 06 | [Processes & Job Control](./06-processes/) | Inspect/manage processes, signals, priorities | 2 h |
| 07 | [Package Management](./07-package-management/) | `apt`/`dnf`/`rpm`/`dpkg`; repos; from source | 2 h |

### Phase 2 — Linux Administration (LPIC-1 102 + Linux+)
| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 08 | [Boot, systemd & Services](./08-systemd-and-services/) | Boot flow; `systemctl`; units; `journalctl` | 2.5 h |
| 09 | [Storage & Filesystems](./09-storage-filesystems/) | Partitions, filesystems, `fstab`, LVM, swap | 3 h |
| 10 | [Networking](./10-networking/) | IP/routing/DNS; `ip`/`ss`; firewalls | 3 h |
| 11 | [Scheduling, Logging & Backups](./11-scheduling-logging-backups/) | cron, systemd timers, logs, `rsync` backups | 2 h |
| 12 | [Shell Scripting](./12-shell-scripting/) | Write robust bash scripts | 3 h |
| 13 | [SSH & Remote Access](./13-ssh-remote-access/) | Key auth, `~/.ssh/config`, tunnels, hardening | 2 h |
| 14 | [Security & Hardening](./14-security-hardening/) | sudo policy, firewall, fail2ban, SELinux/AppArmor | 2.5 h |
| 15 | [Containers & Virtualization (and more)](./15-containers-virtualization/) | namespaces/cgroups; Podman/Docker basics | 1.5 h |

### Capstone
| # | Module | You'll… | Est. |
|---|--------|---------|------|
| 16 | [Capstone: Build & Harden a Server](./16-capstone/) | Stand up a firewalled web server with users, storage, logging, and backups — by hand | 3+ h |

**Total: a realistic ~35 hours.** It's a big course — take it in phases.

**→ Then automate it all in the separate [Ansible course](../ansible-course/).**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts + distro call-outs. Read first.
├── lab.md         ← Step-by-step guided lab with expected output. Do second.
├── code/          ← Scripts/configs/playbooks the lab uses (where applicable).
├── challenge.md   ← An unguided task. Do third.
└── solutions/     ← Reference answers — peek only after trying.
```

---

## Reference material (keep open)

- **[cheatsheets/command-reference.md](./cheatsheets/command-reference.md)** — the commands you'll use daily
- **[cheatsheets/permissions.md](./cheatsheets/permissions.md)** — chmod/chown/special bits, fast
- **[cheatsheets/regex-and-text.md](./cheatsheets/regex-and-text.md)** — grep/sed/awk + regex
- **[cheatsheets/distro-differences.md](./cheatsheets/distro-differences.md)** — Debian vs RHEL family cross-reference
- **[GLOSSARY.md](./GLOSSARY.md)** — every term in plain English
- **[VERIFY.md](./VERIFY.md)** — confirm your environment works

---

## Quick start

```bash
cd linux-course/00-setup
cat README.md            # spin up a Linux VM on your Mac
cd ../01-shell-command-line && cat README.md
```

Ready? **→ [Start with Module 00: Setup & Orientation](./00-setup/)**
