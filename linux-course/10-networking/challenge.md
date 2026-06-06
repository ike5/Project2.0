# Challenge 10 — Network Diagnosis

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Subnet math.** For `10.20.30.45/26`: what is the network address, the broadcast
   address, the usable host range, and how many usable hosts? Show your reasoning.

2. **Who owns the port?** A service is failing to start because "port 8080 is already in
   use." Write the single command that shows which process (PID + name) is listening on
   8080.

3. **Layered triage.** A user reports "the website is down." Give an ordered list of
   commands to isolate whether the problem is: the local stack, the gateway, routing/
   internet, DNS, or the web service — and what each result would tell you.

4. **Firewall rule.** Allow inbound SSH only from the subnet `192.168.50.0/24`, and HTTP/
   HTTPS from anywhere. Give the `ufw` commands (and the firewalld equivalent for HTTP).

5. **DNS override.** Make `api.internal` resolve to `10.0.0.5` on this host only, then
   verify, then remove it. Which file, and why does it take effect immediately?

## Success criteria
- [ ] Correct /26 subnet breakdown (network .0? compute it; 62 usable hosts).
- [ ] `sudo ss -tlpn | grep :8080` (or `lsof -i :8080`).
- [ ] Sensible ordered triage (`ping 127.0.0.1` → gateway → `1.1.1.1` → `dig` → `curl`).
- [ ] Correct `ufw allow from 192.168.50.0/24 to any port 22 proto tcp` etc.
- [ ] `/etc/hosts` edit, verified with `getent hosts api.internal`.
