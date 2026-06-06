# Ansible: Automate Your Infrastructure ⚙️🤖

A hands-on course that takes you from zero to **automating real Linux servers with
Ansible** — inventories, idempotent playbooks, templates, roles, and secrets — finishing
with a multi-host deployment you build yourself.

> **Who this is for:** You're comfortable on the Linux command line and SSH (if not, do
> the **[Linux course](../linux-course/)** first — it's the perfect prerequisite, and
> Ansible automates exactly the work you learn there). No prior Ansible needed.

---

## Why Ansible

You *can* configure servers by hand (SSH in, edit files, install packages, restart
services). It doesn't scale, drifts over time, and isn't reviewable. **Ansible** lets you
describe the desired state of your servers as **code** that is:

- **Agentless** — it just uses **SSH** + Python; nothing to install on the managed hosts.
- **Idempotent** — run it 10 times, the result is the same; it only changes what's needed.
- **Declarative-ish** — you describe *what* you want; modules figure out *how*.
- **Readable** — plain YAML your team can review, version, and reuse.

```
   Control node (you)                 Managed nodes
 ┌────────────────────┐   SSH    ┌───────────────────────────┐
 │ ansible + playbooks│ ───────▶ │ web01   web02   db01 ...  │
 │ inventory + roles  │          │ (just need Python + sshd) │
 └────────────────────┘          └───────────────────────────┘
```

---

## What makes it effective

- **Learn by doing.** Every module = concepts + a guided lab against real hosts + an
  unguided challenge + reference solutions.
- **Idempotence first.** You'll *see* tasks report `changed` once and `ok` forever after —
  the core Ansible mindset.
- **Build up a real project.** Each module grows a `webstack` project: from a single ad-hoc
  command to a roled, vaulted, multi-host deployment.
- **A capstone.** Deploy a load-balanced web app (reverse proxy + two app servers) entirely
  with Ansible.

---

## Prerequisites

- A **control node**: Linux or macOS with Python 3 (where Ansible runs).
- **One or two managed Linux hosts** to automate — VMs (Multipass), cloud servers, or
  containers. Module 00 sets this up.
- **SSH key access** from the control node to the managed hosts (Module 00 covers it).

Versions: **ansible-core 2.16+** (the `ansible` package), targeting **Ubuntu 22.04**
managed hosts (RHEL-family notes included).

---

## The learning path

| # | Module | You'll learn to… | Est. |
|---|--------|------------------|------|
| 00 | [Setup & First Contact](./00-setup/) | Install Ansible; define an inventory; `ping` your hosts | 1 h |
| 01 | [Inventory & Ad-Hoc Commands](./01-inventory-adhoc/) | Group hosts; run one-off module commands | 1.5 h |
| 02 | [Playbooks, Tasks & Idempotence](./02-playbooks/) | Write idempotent playbooks; handlers; check mode | 3 h |
| 03 | [Variables, Facts & Templates](./03-variables-facts-templates/) | Parameterize with vars/facts; Jinja2 templates; loops | 3 h |
| 04 | [Roles & Reuse](./04-roles/) | Structure reusable roles; Ansible Galaxy | 3 h |
| 05 | [Vault, Testing & Best Practices](./05-vault-best-practices/) | Encrypt secrets; lint/check; project layout | 2.5 h |
| 06 | [Capstone: Multi-Host Deploy](./06-capstone/) | Ship a reverse proxy + 2 app servers | 3+ h |

**Total: a realistic ~17 hours.**

---

## How each module is structured

```
NN-topic/
├── README.md      ← Concepts. Read first.
├── lab.md         ← Step-by-step guided lab with expected output. Do second.
├── code/          ← Inventories, playbooks, templates, roles the lab uses.
├── challenge.md   ← An unguided task. Do third.
└── solutions/     ← Reference answers — peek only after trying.
```

---

## Reference material

- **[cheatsheets/ansible.md](./cheatsheets/ansible.md)** — CLI, playbook, and module reference
- **[cheatsheets/jinja2.md](./cheatsheets/jinja2.md)** — templating syntax
- **[GLOSSARY.md](./GLOSSARY.md)** — every term in plain English
- **[VERIFY.md](./VERIFY.md)** — confirm your control node + hosts work

## Quick start

```bash
cd ansible-course/00-setup
cat README.md            # install Ansible and define your inventory
ansible all -m ping      # once set up: pings every managed host
```

Ready? **→ [Start with Module 00: Setup & First Contact](./00-setup/)**
