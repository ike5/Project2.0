# Module 13 — SSH & Remote Access

**Goal:** connect to and manage remote machines securely with SSH — key auth, config,
file transfer, tunnels, and hardening. This is the foundation the Ansible course builds
on (Ansible is "SSH + automation"). ⏱️ ~2 h · 🎯 Prereq: 00–12.

---

## 1. SSH basics

**SSH** gives you an encrypted shell on a remote host.
```bash
ssh user@host                 # connect (prompts for password by default)
ssh -p 2222 user@host         # non-default port
ssh user@host 'uptime'        # run one command and return
ssh user@host 'hostname; df -h /'    # multiple commands
```
The first connection asks you to trust the host's fingerprint (stored in
`~/.ssh/known_hosts`).

## 2. Key-based authentication (do this — it's better than passwords)

A **keypair**: a **private** key (stays secret on your machine) and a **public** key (you
put on servers). The server proves you hold the private key — no password sent.
```bash
ssh-keygen -t ed25519 -C "you@example"     # generate (accept defaults; set a passphrase)
# creates ~/.ssh/id_ed25519 (private) and id_ed25519.pub (public)
ssh-copy-id user@host                        # install your public key on the server
ssh user@host                                # now logs in with the key, no password
```
Do it manually if `ssh-copy-id` isn't available: append your `.pub` to the server's
`~/.ssh/authorized_keys` (perms: `~/.ssh` 700, `authorized_keys` 600).

> The **ssh-agent** caches your decrypted private key so you enter the passphrase once:
> `eval "$(ssh-agent)"; ssh-add ~/.ssh/id_ed25519`.

## 3. The client config: `~/.ssh/config`

Stop retyping hosts/users/ports/keys:
```
Host web
    HostName 192.168.50.10
    User deploy
    Port 22
    IdentityFile ~/.ssh/id_ed25519

Host *.lab
    User ubuntu
    StrictHostKeyChecking accept-new
```
Now just: `ssh web`. (Ansible uses this same config and keys.)

## 4. File transfer

```bash
scp file user@host:/path/                 # copy a file to the server
scp -r dir user@host:/path/               # recursive
scp user@host:/etc/hostname .             # copy FROM the server
rsync -avz -e ssh local/ user@host:/remote/   # efficient sync over ssh
sftp user@host                             # interactive file transfer
```

## 5. Tunnels (port forwarding)

```bash
# Local forward: reach a remote-only service via localhost
ssh -L 8080:localhost:80 user@host         # local 8080 -> host's port 80
# Remote forward: expose a local service on the remote
ssh -R 9000:localhost:3000 user@host
# Jump host (bastion):
ssh -J bastion user@internal-host
ssh -D 1080 user@host                      # SOCKS proxy (dynamic)
```

## 6. Hardening sshd (server side)

Edit `/etc/ssh/sshd_config`, then `sudo systemctl restart ssh`:
```
PermitRootLogin no                 # no direct root login
PasswordAuthentication no          # keys only (set up keys FIRST!)
PubkeyAuthentication yes
AllowUsers deploy ubuntu           # restrict who can log in
Port 22                            # (changing it is obscurity, not security)
```
> ⚠️ Before setting `PasswordAuthentication no`, **confirm key login works in a second
> session** — or you can lock yourself out. Keep a session open while testing.

## 7. Persistent sessions

`ssh` drops if the connection breaks. Use **tmux** (or screen) on the server so work
survives disconnects:
```bash
tmux            # start;  Ctrl+b d to detach;  tmux attach to resume
```

---

## Do the lab
Set up key auth between two VMs, write an `~/.ssh/config`, transfer files, build a
tunnel, and harden sshd. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
ssh · key pair (private/public) · `ssh-keygen`/`ssh-copy-id`/`authorized_keys` · ssh-agent ·
`~/.ssh/config` · `scp`/`sftp`/`rsync -e ssh` · port forwarding (`-L`/`-R`/`-D`/`-J`) ·
`sshd_config` hardening (`PermitRootLogin`/`PasswordAuthentication`) · tmux

**Next →** [Module 14: Security & Hardening](../14-security-hardening/)
