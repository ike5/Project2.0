"""
apps/pulse/chat/partitions.py — partition maintenance and retention.

A partitioned table is a promise to the future: tomorrow's partition must exist
before tomorrow. If it does not, one of two things happens and both are bad.

  * No DEFAULT partition  -> inserts FAIL at midnight:
        ERROR: no partition of relation "messages" found for row
    Loud, immediate, attributable. This is what Pulse chooses.

  * A DEFAULT partition   -> inserts land there SILENTLY, and every property
    partitioning bought you is quietly undone. Worse, once the default has rows,
    ATTACHing a partition that overlaps its range makes Postgres scan the whole
    default under an ACCESS EXCLUSIVE lock to prove no row belongs in the new
    range — a multi-minute outage triggered by a routine maintenance task.

A failed insert at 00:00:01 is a page. A silent default partition is a bad
quarter.

Run it from Celery beat (recommended) or as a management command:

    python manage.py maintain_partitions --ahead 3 --retain 90
    python manage.py maintain_partitions --ahead 3 --retain 90 --dry-run
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import date, timedelta

from celery import shared_task
from django.db import connection
from prometheus_client import Gauge

log = logging.getLogger("pulse.partitions")

TABLE = "messages"
MONTHS_AHEAD = 3      # 3 is not arbitrary: it survives a task that has been
                      # broken for two months without anyone noticing, which is
                      # the realistic failure mode for a task nobody watches.
RETAIN_DAYS = 90

_partition_count = Gauge("pulse_partitions_total", "attached partitions")
_oldest_partition_days = Gauge(
    "pulse_partition_oldest_age_days", "age of the oldest attached partition")
_months_ahead = Gauge(
    "pulse_partitions_months_ahead", "months of future partitions that exist")


@dataclass(frozen=True)
class Bound:
    name: str
    start: date
    end: date

    @classmethod
    def for_month(cls, d: date) -> "Bound":
        start = d.replace(day=1)
        end = (start + timedelta(days=32)).replace(day=1)
        return cls(f"{TABLE}_{start:%Y_%m}", start, end)


def _existing() -> set[str]:
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT c.relname
              FROM pg_class c
              JOIN pg_inherits i ON i.inhrelid = c.oid
              JOIN pg_class p ON p.oid = i.inhparent
             WHERE p.relname = %s
            """,
            [TABLE],
        )
        return {row[0] for row in cur.fetchall()}


def create_ahead(months: int = MONTHS_AHEAD, dry_run: bool = False) -> list[str]:
    existing = _existing()
    created = []
    cursor_date = date.today()
    for _ in range(months + 1):
        b = Bound.for_month(cursor_date)
        if b.name not in existing:
            sql = (
                f'CREATE TABLE IF NOT EXISTS "{b.name}" '
                f'PARTITION OF "{TABLE}" '
                f"FOR VALUES FROM ('{b.start:%Y-%m-%d}') TO ('{b.end:%Y-%m-%d}')"
            )
            log.info("creating partition %s", b.name)
            if not dry_run:
                with connection.cursor() as cur:
                    # CREATE TABLE ... PARTITION OF on a NEW (empty) range takes
                    # only a brief lock on the parent. This is the cheap path.
                    # CREATE + ATTACH of a table that already has rows is the
                    # expensive one (Postgres validates the constraint) — use
                    # ATTACH with a matching CHECK constraint already in place to
                    # skip the scan. Lab Part B does exactly that when it
                    # converts the existing table.
                    cur.execute(sql)
            created.append(b.name)
        cursor_date = b.end
    return created


def drop_expired(retain_days: int = RETAIN_DAYS, dry_run: bool = False) -> list[str]:
    """
    The entire reason to partition. This is O(1) regardless of table size.

    DETACH first, then DROP, deliberately:
      * DETACH CONCURRENTLY takes no long lock on the parent, so live traffic is
        unaffected;
      * the detached table is then an ordinary table you can inspect, dump, or
        keep for a week before dropping.
    A straight `DROP TABLE messages_2026_05` also works and is instant, but it is
    irreversible at 3 a.m., which is when retention jobs run.
    """
    cutoff = date.today() - timedelta(days=retain_days)
    dropped = []
    for name in sorted(_existing()):
        try:
            _, year, month = name.rsplit("_", 2)
            end = (date(int(year), int(month), 1) + timedelta(days=32)).replace(day=1)
        except ValueError:
            log.warning("unrecognized partition name %s — skipping", name)
            continue
        if end <= cutoff:
            log.info("dropping partition %s (ends %s, cutoff %s)", name, end, cutoff)
            if not dry_run:
                with connection.cursor() as cur:
                    cur.execute(
                        f'ALTER TABLE "{TABLE}" DETACH PARTITION "{name}" CONCURRENTLY')
                    cur.execute(f'DROP TABLE "{name}"')
            dropped.append(name)
    return dropped


def report() -> dict:
    existing = _existing()
    _partition_count.set(len(existing))
    months = 0
    cursor_date = date.today()
    while Bound.for_month(cursor_date).name in existing:
        months += 1
        cursor_date = Bound.for_month(cursor_date).end
    _months_ahead.set(months - 1)

    if existing:
        oldest = min(existing)
        _, year, month = oldest.rsplit("_", 2)
        age = (date.today() - date(int(year), int(month), 1)).days
        _oldest_partition_days.set(age)
    return {"partitions": len(existing), "months_ahead": months - 1}


@shared_task(name="chat.maintain_partitions")
def maintain_partitions(ahead: int = MONTHS_AHEAD, retain: int = RETAIN_DAYS) -> dict:
    created = create_ahead(ahead)
    dropped = drop_expired(retain)
    stats = report()
    return {"created": created, "dropped": dropped, **stats}


# Celery beat, in settings.py:
#
#   CELERY_BEAT_SCHEDULE = {
#       "maintain-partitions": {
#           "task": "chat.maintain_partitions",
#           "schedule": crontab(hour=3, minute=17),   # not :00 — see below
#       },
#   }
#
# ALERT ON months_ahead, NOT ON THE TASK.
#
#   pulse_partitions_months_ahead < 2   for 6 hours   -> warn
#   pulse_partitions_months_ahead < 1   for 1 hour    -> page
#
# A task that stops running raises no error, emits no metric, and produces no
# log line — you cannot alert on the absence of something you never see. You CAN
# alert on the state it was supposed to maintain, and that alert also fires if
# the task ran and did the wrong thing. Alert on the invariant, never on the job.
#
# (crontab minute=17 rather than 0 for the same reason every cron in this course
# avoids the hour boundary: at :00 you are competing with every backup, every
# metrics rollup and every other team's cron on the same box.)
