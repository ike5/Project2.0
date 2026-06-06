# Module 10 — Networking

**Goal:** read and configure Linux networking — addresses, routes, DNS, ports, and
firewalls — and diagnose connectivity. ⏱️ ~3 h · 🎯 Prereq: 00–09.

---

## 1. The essentials of IP

- An **IP address** + **subnet** identifies a host on a network: `192.168.1.10/24`. The
  `/24` (netmask `255.255.255.0`) says the first 24 bits are the **network**, the rest the
  **host** → here, hosts `192.168.1.1`–`.254`.
- The **default gateway** is where packets go when the destination isn't on your subnet.
- **DNS** turns names into IPs.

## 2. Inspect with `ip` (replaces ifconfig/route)

```bash
ip a                 # addresses on all interfaces (ip addr show)
ip -br a             # brief, readable
ip link              # interfaces up/down + MAC
ip route             # the routing table (default via ... )
ip neigh             # ARP/neighbor table
hostname -I          # this host's IPs
```
Temporarily (not persistent) set an address/route:
```bash
sudo ip addr add 192.168.50.10/24 dev eth0
sudo ip link set eth0 up
sudo ip route add default via 192.168.50.1
```

## 3. Persistent configuration

- **Ubuntu (netplan):** edit `/etc/netplan/*.yaml`, then `sudo netplan apply`:
  ```yaml
  network:
    version: 2
    ethernets:
      eth0:
        dhcp4: false
        addresses: [192.168.50.10/24]
        routes: [{to: default, via: 192.168.50.1}]
        nameservers: {addresses: [1.1.1.1, 8.8.8.8]}
  ```
- **RHEL / NetworkManager:** `nmcli`:
  ```bash
  nmcli con mod eth0 ipv4.addresses 192.168.50.10/24 ipv4.gateway 192.168.50.1 ipv4.method manual
  nmcli con up eth0
  ```

## 4. DNS resolution

```bash
cat /etc/resolv.conf           # nameservers (often managed by systemd-resolved)
cat /etc/hosts                 # static name→IP (checked before DNS)
resolvectl status              # systemd-resolved view (Ubuntu)
dig example.com                # full DNS query (ANSWER section)
dig +short example.com
host example.com               # simpler
getent hosts example.com       # uses the system resolver (hosts + DNS)
```
Name lookup order is set in `/etc/nsswitch.conf` (`hosts: files dns`).

## 5. Ports & sockets with `ss`

```bash
ss -tulpn            # TCP/UDP listening sockets + ports + owning process
ss -tn state established     # active TCP connections
ss -s                # summary stats
```
`-t` TCP, `-u` UDP, `-l` listening, `-p` process, `-n` numeric.

## 6. Test connectivity

```bash
ping -c4 1.1.1.1               # is the host reachable? (ICMP)
ping -c4 example.com          # tests DNS + reachability
traceroute example.com        # the path (hops)
mtr example.com               # live traceroute+ping (great)
curl -I https://example.com   # HTTP headers (app-layer test)
curl -v telnet://host:22      # can I reach a port? (or: nc -vz host 22)
nc -vz host 80                # netcat port check
```

## 7. Firewalls

Under the hood is **nftables/iptables**; you usually drive a front-end:
```bash
# Ubuntu — ufw
sudo ufw status verbose
sudo ufw allow 22/tcp                 # SSH
sudo ufw allow 80,443/tcp
sudo ufw enable
# RHEL — firewalld
sudo firewall-cmd --list-all
sudo firewall-cmd --add-service=http --permanent
sudo firewall-cmd --add-port=8080/tcp --permanent
sudo firewall-cmd --reload
```
> Golden rule: **allow SSH (22) before enabling the firewall** on a remote box, or you'll
> lock yourself out.

---

## Do the lab
Inspect interfaces/routes/DNS, find listening services, test connectivity, and configure
a firewall. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
IP/subnet/CIDR · gateway/route · `ip a`/`ip route`/`ip link` · netplan/`nmcli` · DNS ·
`/etc/resolv.conf`/`/etc/hosts`/nsswitch · `dig`/`host`/`getent` · `ss -tulpn` · port ·
`ping`/`traceroute`/`mtr`/`curl`/`nc` · firewall (ufw/firewalld/nftables)

**Next →** [Module 11: Scheduling, Logging & Backups](../11-scheduling-logging-backups/)
