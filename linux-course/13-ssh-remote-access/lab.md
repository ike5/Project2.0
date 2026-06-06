# Lab 13 — SSH Between Two Machines

**You'll:** set up key auth from `lab` → `web`, configure a host alias, transfer files,
build a tunnel, and harden sshd. ⏱️ ~55 min.

> Needs **two** VMs. From Module 00: `multipass launch --name web 22.04`.
> Find each IP with `multipass list`. We'll connect *from* `lab` *to* `web`.

---

## Part A — First connection (password)
On `web`, set a password for the `ubuntu` user so we can bootstrap:
```bash
multipass shell web
sudo passwd ubuntu          # set a temporary password
# enable password auth temporarily if needed, then exit back to your Mac
exit
```
From `lab` (`multipass shell lab`):
```bash
WEB_IP=<web's IP from multipass list>
ssh ubuntu@"$WEB_IP"        # accept the fingerprint, enter the password, then 'exit'
```
✅ You reached `web` over SSH.

## Part B — Key-based auth
On `lab`:
```bash
ssh-keygen -t ed25519 -C "lab-to-web"      # press Enter through prompts (passphrase optional)
ssh-copy-id ubuntu@"$WEB_IP"               # installs your public key on web
ssh ubuntu@"$WEB_IP" 'hostname'            # logs in with the KEY now (no password) -> 'web'
```
✅ No password prompt — the key authenticated you. Confirm on `web`:
```bash
ssh ubuntu@"$WEB_IP" 'cat ~/.ssh/authorized_keys'   # your public key is there
```

## Part C — ~/.ssh/config alias
On `lab`:
```bash
cat >> ~/.ssh/config <<EOF
Host web
    HostName $WEB_IP
    User ubuntu
    IdentityFile ~/.ssh/id_ed25519
EOF
chmod 600 ~/.ssh/config
ssh web 'uptime'           # just 'ssh web' now
```
✅ The alias resolves host/user/key — exactly what Ansible will use.

## Part D — Transfer files
```bash
echo "deployed at $(date)" > release.txt
scp release.txt web:/tmp/                   # copy to web
ssh web 'cat /tmp/release.txt'
scp web:/etc/os-release ./web-os-release    # copy from web
rsync -avz ./ web:/tmp/labsync/             # sync this dir to web
ssh web 'ls /tmp/labsync | head'
```

## Part E — A tunnel
```bash
# On web, start a simple service bound to localhost only:
ssh web 'nohup python3 -m http.server 8000 --bind 127.0.0.1 >/tmp/srv.log 2>&1 &'
# It's NOT reachable from lab directly (bound to web's localhost). Tunnel it:
ssh -fN -L 8080:localhost:8000 web          # background local-forward
curl -s localhost:8080 | head -3            # you reach web's localhost:8000 via the tunnel!
# stop the tunnel:
pkill -f 'ssh -fN -L 8080'
ssh web 'pkill -f http.server'
```
✅ Local forwarding let you reach a service that only listens on the remote's loopback.

## Part F — Harden sshd (carefully)
```bash
ssh web   # interactive session — KEEP THIS OPEN while testing
sudo sed -i 's/^#\?PermitRootLogin.*/PermitRootLogin no/' /etc/ssh/sshd_config
sudo sed -i 's/^#\?PasswordAuthentication.*/PasswordAuthentication no/' /etc/ssh/sshd_config
sudo sshd -t                 # TEST the config syntax (no output = OK)
sudo systemctl restart ssh
# In a SECOND terminal, confirm key login still works BEFORE closing the first:
#   ssh web 'echo still-in'
```
✅ Root login disabled and password auth off — **key-only**. The "keep one session open +
test in a second" habit prevents lockouts.

## What you learned
- Bootstrap with a password, then switch to **key auth** (`ssh-keygen`/`ssh-copy-id`).
- `~/.ssh/config` aliases; `scp`/`rsync` transfers.
- Local port forwarding to reach loopback-only services.
- Hardening `sshd` safely (`sshd -t`, test in a second session).

➡️ **[challenge.md](./challenge.md)** then [Module 14](../14-security-hardening/).
