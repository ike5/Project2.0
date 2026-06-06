# Challenge 11 — Automate the Boring Stuff

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Cron expressions.** Write the cron time fields for: (a) every weekday at 6:30 PM,
   (b) every 5 minutes, (c) the 1st of each month at midnight, (d) every Sunday at 03:15.

2. **cron vs timer.** Give two concrete advantages a **systemd timer** has over a cron
   job, and one reason you might still choose cron.

3. **A real timer.** Convert the lab's `backup.sh` to run **daily at 02:00** via a
   systemd timer (write both the `.service` and `.timer`). Make it "catch up" if the
   machine was off at 02:00.

4. **rsync correctness.** Explain the difference in result between
   `rsync -a /src /dst` and `rsync -a /src/ /dst`. Then give the command to **mirror**
   `/src` into `/dst` such that files deleted from `/src` are also removed from `/dst`,
   with a preview first.

5. **Retention.** The lab script keeps the 7 newest backups. Explain the pipeline
   `ls -1t ... | tail -n +8 | xargs -r rm -f` piece by piece (what each stage does and why
   `-r` matters).

## Success criteria
- [ ] All four cron expressions correct.
- [ ] Two timer advantages + one cron advantage.
- [ ] Working daily backup `.service` + `.timer` with `Persistent=true`.
- [ ] Correct trailing-slash explanation and a safe `--delete` mirror with `-n` preview.
- [ ] Accurate breakdown of the retention pipeline.
