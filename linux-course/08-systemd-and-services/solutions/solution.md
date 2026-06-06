# Challenge 08 — Reference Solution

### 1. pyweb.service
`/etc/systemd/system/pyweb.service`:
```ini
[Unit]
Description=Simple Python web server
After=network-online.target
Wants=network-online.target

[Service]
WorkingDirectory=/srv/www
ExecStart=/usr/bin/python3 -m http.server 8000
Restart=on-failure
User=nobody
Group=nogroup

[Install]
WantedBy=multi-user.target
```
```bash
sudo mkdir -p /srv/www && echo "hi" | sudo tee /srv/www/index.html
sudo systemctl daemon-reload
sudo systemctl enable --now pyweb
curl -s localhost:8000           # shows 'hi'
# prove restart:
sudo kill -9 "$(systemctl show -p MainPID --value pyweb)"; sleep 2
curl -s localhost:8000           # back up
```

### 2. Ordering & deps
> - **`After=network-online.target`** controls **ordering** only — start pyweb *after*
>   that target is reached (with `Wants=network-online.target` to actually pull it in).
> - **`Requires=`** adds a **hard dependency**: if the required unit fails to start (or is
>   stopped), this unit is stopped too. `After` does *not* imply a dependency, and
>   `Requires` does *not* imply ordering — you often use both together.

### 3. Boot timing
```bash
systemd-analyze                 # total boot time breakdown
systemd-analyze blame           # each unit sorted by startup time (slowest first)
systemd-analyze critical-chain  # the dependency chain that gated boot
```
> `blame` ranks units by how long they took to initialize — the first place to look when
> boot is slow.

### 4. Override via drop-in
```bash
sudo systemctl edit pyweb       # opens an editor for a drop-in
# add:
[Service]
Restart=always
RestartSec=5
```
> This creates `/etc/systemd/system/pyweb.service.d/override.conf`. The vendor unit in
> `/lib/systemd/system/` stays untouched, so **package updates won't clobber your change**
> and your override is clearly separated. `systemctl daemon-reload` is run for you by
> `edit`.

### 5. Crash investigation
```bash
journalctl -u pyweb -b -p err -f
```
(`-u` the unit, `-b` since boot, `-p err` errors+worse, `-f` follow.)
