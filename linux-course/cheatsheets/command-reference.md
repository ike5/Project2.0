# Command Reference Cheatsheet

The everyday commands, grouped by job. `man <cmd>` or `<cmd> --help` for details.

## Getting help & orientation
```bash
man ls            # manual page         (q to quit, /word to search)
ls --help         # quick usage
type cmd          # is it a builtin/alias/binary?
which cmd         # path to the binary
apropos network   # search man pages by keyword
whoami; id        # who am I; my uid/gids
uname -a          # kernel/OS info
hostnamectl       # host + OS details
```

## Navigation & files
```bash
pwd                       # current directory
cd /etc;  cd ~;  cd -     # change dir; home; previous
ls -lah                   # long, all (incl. dotfiles), human sizes
tree -L 2                 # directory tree (if installed)
cp -r src dst             # copy (recursive)
mv a b                    # move/rename
rm -rf dir                # remove recursively (careful!)
mkdir -p a/b/c            # make nested dirs
touch file                # create/update timestamp
ln -s target linkname     # symbolic link
stat file                 # detailed metadata
file thing                # guess file type
find /etc -name '*.conf'  # find by name
find . -type f -mtime -1  # files modified < 1 day ago
locate sshd_config        # fast index search (updatedb)
du -sh *                  # sizes of items here
df -h                     # filesystem free space
```

## Viewing & editing text
```bash
cat f;  less f;  head -n 20 f;  tail -n 20 f;  tail -f log
nano f;  vim f            # editors
wc -l f                   # count lines
diff a b;  cmp a b        # compare
```

## Pipelines & text tools (see regex-and-text.md)
```bash
grep -ri "error" /var/log         # recursive, case-insensitive search
sed 's/old/new/g' f               # stream edit
awk -F: '{print $1}' /etc/passwd  # field extraction
cut -d, -f1,3 data.csv            # columns
sort | uniq -c | sort -rn         # frequency count
tr 'a-z' 'A-Z'                    # translate chars
xargs                             # build commands from stdin
tee file                          # split output to file + stdout
```

## Users & permissions (see permissions.md)
```bash
sudo -i                    # root shell
adduser sam                # create user (Debian friendly)  / useradd on RHEL
passwd sam                 # set password
usermod -aG sudo sam       # add to a group
chmod 640 f;  chmod u+x f  # octal / symbolic
chown sam:devs f           # owner:group
umask                      # default-permission mask
```

## Processes & resources
```bash
ps aux                     # all processes
ps -ef --forest            # process tree
top;  htop                 # live monitor
kill -TERM 1234;  kill -9 1234
pkill -f pattern;  pgrep -fa pattern
jobs;  fg %1;  bg %1;  cmd &;  nohup cmd &
nice -n 10 cmd;  renice -n 5 -p PID
free -h;  vmstat 1;  uptime
```

## Packages (see distro-differences.md)
```bash
# Debian/Ubuntu
sudo apt update && sudo apt upgrade
sudo apt install nginx;  apt search word;  apt show pkg;  sudo apt remove pkg
# RHEL/Fedora
sudo dnf install nginx;  dnf search word;  dnf info pkg;  sudo dnf remove pkg
```

## Services (systemd)
```bash
systemctl status sshd
sudo systemctl start|stop|restart|reload sshd
sudo systemctl enable|disable --now sshd
systemctl list-units --type=service
journalctl -u sshd -e          # logs for a unit (end)
journalctl -f                  # follow all logs
```

## Networking
```bash
ip a;  ip route;  ip -br link
ss -tulpn                      # listening sockets + ports + pids
ping -c3 host;  traceroute host
dig example.com;  host example.com;  getent hosts name
curl -I https://example.com;  wget url
sudo ufw status;  sudo firewall-cmd --list-all
```

## Disks & storage
```bash
lsblk;  blkid;  fdisk -l
sudo mount /dev/sdb1 /mnt;  umount /mnt
sudo mkfs.ext4 /dev/sdb1
swapon --show;  free -h
```

## Archives & transfer
```bash
tar -czf out.tgz dir/;  tar -xzf out.tgz   # gzip create/extract
zip -r out.zip dir/;  unzip out.zip
rsync -avh --delete src/ dst/              # sync (trailing slash matters)
scp file user@host:/path                   # copy over ssh
```

## The terminal itself
```bash
Ctrl+C  interrupt    Ctrl+D  EOF/logout    Ctrl+Z  suspend job
Ctrl+R  search history    Ctrl+A/E  start/end of line    Ctrl+L  clear
!!  last command    !$  last arg    history    sudo !!  rerun as root
```
