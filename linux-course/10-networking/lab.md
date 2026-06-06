# Lab 10 — Networking & Firewall

**You'll:** inspect networking, resolve names, find listening ports, test connectivity,
and set up a firewall. ⏱️ ~55 min. In your VM.

---

## Part A — Who am I on the network
```bash
ip -br a                       # interfaces + addresses (brief)
ip route                       # note 'default via ...' = your gateway
hostname -I                    # this host's IP(s)
ip neigh                       # neighbors (ARP)
```

## Part B — DNS
```bash
cat /etc/resolv.conf
cat /etc/hosts
getent hosts ubuntu.com        # system resolver (files + DNS)
dig +short ubuntu.com
dig ubuntu.com | sed -n '/ANSWER SECTION/,/^$/p'
# Add a static host mapping and test it:
echo "127.0.0.1 myapp.local" | sudo tee -a /etc/hosts
getent hosts myapp.local       # resolves to 127.0.0.1 (from /etc/hosts, before DNS)
sudo sed -i '/myapp.local/d' /etc/hosts   # clean up
```
✅ `/etc/hosts` wins over DNS — handy for testing and overrides.

## Part C — What's listening
```bash
sudo ss -tulpn                 # all listening TCP/UDP + the process
sudo ss -tlpn | grep ':22'     # sshd on port 22
ss -tn state established | head # active connections
```

## Part D — Start a service and reach it
```bash
sudo apt install -y nginx
systemctl is-active nginx
sudo ss -tlpn | grep ':80'     # nginx listening on 80
curl -I localhost              # HTTP/1.1 200 OK (or 301) from nginx
curl -s localhost | head -5
```

## Part E — Connectivity tests
```bash
ping -c3 127.0.0.1             # loopback (always works if stack is up)
ping -c3 "$(ip route | awk '/default/{print $3}')"   # your gateway
ping -c3 1.1.1.1              # the internet by IP (no DNS)
ping -c3 ubuntu.com           # by name (tests DNS too)
curl -I https://ubuntu.com    # app-layer reachability
nc -vz localhost 80           # port check (connection succeeded)
```
✅ Distinguish layers: loopback (stack), gateway (LAN), IP ping (routing), name ping
(DNS), curl (application).

## Part F — Firewall (ufw)
```bash
sudo ufw allow 22/tcp          # ALLOW SSH FIRST (don't lock yourself out!)
sudo ufw allow 80/tcp
sudo ufw --force enable
sudo ufw status verbose
# Prove it: block 80, see curl fail, then re-allow
sudo ufw deny 80/tcp
sudo ufw status | grep 80
curl -m 3 -I localhost || echo "blocked as expected"
sudo ufw allow 80/tcp
curl -I localhost
```
> **RHEL:** `firewall-cmd --add-service=ssh --permanent`,
> `firewall-cmd --add-service=http --permanent`, `firewall-cmd --reload`.

## Cleanup
```bash
sudo ufw --force reset
sudo apt remove -y nginx
```

## What you learned
- `ip`/`ss` to read addresses, routes, and listening sockets.
- DNS resolution and the `/etc/hosts` override.
- Layered connectivity testing (loopback → gateway → IP → name → app).
- ufw/firewalld basics — and to **allow SSH before enabling**.

➡️ **[challenge.md](./challenge.md)** then [Module 11](../11-scheduling-logging-backups/).
