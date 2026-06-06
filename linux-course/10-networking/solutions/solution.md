# Challenge 10 — Reference Solution

### 1. Subnet math for `10.20.30.45/26`
- `/26` → netmask `255.255.255.192`; the last octet has **block size 64** (256 − 192).
- Blocks in the last octet: 0–63, 64–127, 128–191, 192–255. `45` falls in **0–63**.
- **Network:** `10.20.30.0` · **Broadcast:** `10.20.30.63`
- **Usable hosts:** `10.20.30.1` – `10.20.30.62` → **62 usable** (64 − 2 for network &
  broadcast).
```bash
ipcalc 10.20.30.45/26     # confirms, if installed
```

### 2. Who owns the port
```bash
sudo ss -tlpnH 'sport = :8080'      # or: sudo ss -tlpn | grep :8080
# alternative:
sudo lsof -i :8080
```

### 3. Layered triage ("website is down")
```bash
ping -c2 127.0.0.1                       # local TCP/IP stack up?  (fail = local issue)
ping -c2 $(ip route|awk '/default/{print $3}')   # gateway reachable?  (LAN/link)
ping -c2 1.1.1.1                         # internet by IP?  (routing/ISP)
dig +short example.com                   # DNS resolving?   (name service)
curl -I https://example.com              # the web service itself responding?
sudo ss -tlpn | grep ':443'             # (on the server) is it even listening?
```
> Each step isolates a layer: stack → link → routing → DNS → application. The **first**
> step that fails localizes the fault.

### 4. Firewall rules
```bash
# ufw — SSH only from a subnet, HTTP/HTTPS from anywhere:
sudo ufw allow from 192.168.50.0/24 to any port 22 proto tcp
sudo ufw allow 80,443/tcp
sudo ufw enable
# firewalld equivalent for HTTP (+ a rich rule for scoped SSH):
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --add-rich-rule='rule family=ipv4 source address=192.168.50.0/24 service name=ssh accept' --permanent
sudo firewall-cmd --reload
```

### 5. DNS override
```bash
echo "10.0.0.5 api.internal" | sudo tee -a /etc/hosts
getent hosts api.internal        # 10.0.0.5  (resolves immediately)
sudo sed -i '/api.internal/d' /etc/hosts
```
> `/etc/hosts` is consulted **before DNS** (per `hosts: files dns` in
> `/etc/nsswitch.conf`) and is read on each lookup, so there's no service to restart —
> the change is effective immediately.
