# Challenge 13 — Reference Solution

### 1. Dedicated deploy key
```bash
ssh-keygen -t ed25519 -f ~/.ssh/deploy_key -C "deploy@web"   # separate key
# on web:
ssh web 'sudo useradd -m -s /bin/bash deploy && sudo mkdir -p /home/deploy/.ssh'
# install the public key for deploy:
ssh-copy-id -i ~/.ssh/deploy_key.pub deploy@<web-ip>    # if deploy has a temp password
# or push it manually:
cat ~/.ssh/deploy_key.pub | ssh web 'sudo tee -a /home/deploy/.ssh/authorized_keys >/dev/null
  sudo chown -R deploy:deploy /home/deploy/.ssh
  sudo chmod 700 /home/deploy/.ssh; sudo chmod 600 /home/deploy/.ssh/authorized_keys'
```
`~/.ssh/config`:
```
Host deploy-web
    HostName <web-ip>
    User deploy
    IdentityFile ~/.ssh/deploy_key
```
```bash
ssh deploy-web 'whoami'    # deploy
```

### 2. One-shot remote audit
```bash
ssh web 'echo "host: $(hostname)"; echo "up: $(uptime -p)"; df -h / | tail -1'
```

### 3. Jump host
```bash
ssh -J bastionuser@bastion web        # one-liner
```
`~/.ssh/config`:
```
Host web
    HostName 10.0.0.20
    User ubuntu
    ProxyJump bastionuser@bastion
```

### 4. Lockout-proof hardening (order matters)
1. **Set up and verify key auth** for your user first (`ssh-copy-id`; confirm
   `ssh host` logs in with no password).
2. Open a **second** SSH session and keep it connected.
3. Edit `/etc/ssh/sshd_config`: `PasswordAuthentication no`, `PermitRootLogin no`.
4. **Validate**: `sudo sshd -t` (or `sudo sshd -T` to dump effective config). No output =
   syntax OK.
5. `sudo systemctl reload ssh` (reload keeps existing sessions).
6. In a **new** terminal, test `ssh host 'echo ok'` **before** closing your other
   sessions. If it fails, you still have a live session to revert.

### 5. Permissions gotcha
SSH refuses keys if `~/.ssh` or `authorized_keys` are too permissive or wrongly owned:
```bash
chmod 700 ~/.ssh
chmod 600 ~/.ssh/authorized_keys
chown -R "$USER:$USER" ~/.ssh
```
> SSH ignores `authorized_keys` if the file/dir is group- or world-writable, or not owned
> by the user — a deliberate safety check.
