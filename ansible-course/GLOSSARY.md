# Glossary

Plain-English definitions of Ansible terms.

## Core concepts

- **Control node** — the machine where Ansible runs (Linux/macOS + Python). You don't
  install Ansible on the servers you manage.
- **Managed node / host** — a server Ansible configures (needs only SSH + Python).
- **Agentless** — Ansible needs no daemon on managed nodes; it connects over **SSH** and
  runs modules, then cleans up.
- **Inventory** — the list of managed hosts (and groups), in INI or YAML. Default
  `/etc/ansible/hosts`, or `-i inventory`.
- **Group** — a named set of hosts in the inventory (`[web]`, `[db]`). `all` is every host;
  `ungrouped` is hosts in no group.
- **Module** — a unit of work Ansible ships to a host and runs (e.g. `apt`, `copy`,
  `service`, `user`). Modules are **idempotent**.
- **Task** — one invocation of a module with parameters, plus a `name`.
- **Play** — a mapping of a group of hosts to a list of tasks.
- **Playbook** — a YAML file containing one or more plays. The main unit of automation.
- **Ad-hoc command** — a one-off module run from the CLI (`ansible web -m ping`), no
  playbook.
- **Idempotent** — running the same task repeatedly yields the same state; it reports
  `changed` only when it actually changes something.
- **Fact** — a piece of data Ansible auto-discovers about a host (OS, IP, memory),
  available as `ansible_facts` / `ansible_*` variables.
- **Handler** — a task that runs only when **notified** by another task (e.g. "restart
  nginx" after its config changes), and only **once** at the end of the play.
- **Check mode (`--check`)** — a dry run: report what *would* change without changing it.
- **Diff mode (`--diff`)** — show the line-level changes a task would make.

## Variables & templating

- **Variable** — a named value used in tasks/templates (`{{ var }}`). Set in playbooks,
  inventory, `group_vars/`, `host_vars/`, roles, or on the CLI (`-e`).
- **`group_vars/` / `host_vars/`** — directories whose files auto-load variables for a
  group or a host.
- **Variable precedence** — the rules that decide which value wins when a variable is set
  in multiple places (CLI `-e` is highest; role defaults are lowest).
- **Jinja2** — the templating engine: `{{ expression }}`, `{% statement %}`, filters
  (`| default`, `| upper`), used in templates and playbooks.
- **Template (`.j2`)** — a file with Jinja2 placeholders the `template` module renders onto
  a host.
- **Loop** — repeat a task over a list (`loop:`), e.g. install many packages.
- **Conditional (`when:`)** — run a task only if an expression is true.
- **Register** — capture a task's result into a variable for later use.
- **Tag** — a label on tasks so you can run a subset (`--tags`, `--skip-tags`).

## Structure & reuse

- **Role** — a standardized, reusable bundle of tasks/handlers/templates/defaults/vars/
  files under a directory layout (`tasks/`, `handlers/`, `templates/`, `defaults/`, …).
- **`ansible-galaxy`** — the tool + community hub for sharing/installing roles and
  collections.
- **Collection** — a packaged set of modules/roles/plugins (e.g. `community.general`,
  `ansible.posix`), installed with `ansible-galaxy collection install`.
- **`requirements.yml`** — declares roles/collections a project depends on.

## Security & quality

- **Ansible Vault** — encrypts secret files/variables at rest
  (`ansible-vault encrypt/edit/view`), decrypted at run time with a password.
- **`ansible-lint`** — checks playbooks/roles for best-practice and correctness issues.
- **`become`** — privilege escalation (run a task as root/another user via sudo);
  `become: true`, `become_user`.
- **Connection plugin** — how Ansible reaches a host (`ssh` default; `local` for the
  control node; `community.docker.docker` for containers).
- **`ansible.cfg`** — project configuration (inventory path, remote user, SSH settings).
