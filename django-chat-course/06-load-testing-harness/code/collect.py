#!/usr/bin/env python3
"""collect.py -- sample the metrics that predict failure, once a second, to CSV.

A load generator tells you what the client experienced. This tells you why.
Run it for the whole duration of every capacity test; the interesting moment
is always the ten seconds before p99 moved, and you cannot go back for it.

    ./code/collect.py /tmp/run1.csv --pid $(pgrep -f 'uvicorn pulse.asgi' | head -1)
    ./code/collect.py /tmp/run1.csv --url http://localhost:8000/metrics

Columns, in the order you read them during an incident:

    ts            unix seconds
    conns         chat_connections_active  (the denominator for everything)
    loop_lag_ms   chat_event_loop_lag_seconds -- THE LEADING INDICATOR
    in_rate       inbound messages/s, derived from the counter
    out_rate      outbound deliveries/s, derived from the counter
    amp           out_rate / in_rate -- your live amplification factor
    gs_p99_ms     chat_group_send_seconds, p99 estimated from the buckets
    rss_mb        worker RSS from /proc (NOT from Redis or Django)
    kb_per_conn   (rss - baseline) / conns
    cpu_pct       worker CPU as a percentage of ONE core
    gen_cpu_pct   the load generator's CPU -- over ~70% and your run is garbage

Nothing here is Prometheus-specific beyond parsing the text exposition format;
Module 20 replaces it with a real scrape, recording rules and Grafana.
"""

from __future__ import annotations

import argparse
import csv
import os
import re
import sys
import time
import urllib.request

CLOCK_TICKS = os.sysconf("SC_CLK_TCK")
SAMPLE = re.compile(r"^(?P<name>[a-zA-Z_:][\w:]*)(?P<labels>\{[^}]*\})?\s+(?P<value>\S+)$")


def scrape(url: str) -> dict[str, float]:
    """Parse the Prometheus text format into {name_with_labels: value}."""
    out: dict[str, float] = {}
    try:
        with urllib.request.urlopen(url, timeout=2) as fh:
            body = fh.read().decode()
    except Exception:                                        # noqa: BLE001
        return out
    for line in body.splitlines():
        if not line or line.startswith("#"):
            continue
        m = SAMPLE.match(line)
        if not m:
            continue
        try:
            out[m["name"] + (m["labels"] or "")] = float(m["value"])
        except ValueError:
            pass
    return out


def sum_by_name(samples: dict[str, float], name: str) -> float:
    """Sum every labelled series sharing a metric name. Correct for counters
    and for gauges you genuinely want summed (connections); wrong for gauges
    you want the max of -- which is why loop lag is read with max_by_name."""
    return sum(v for k, v in samples.items() if k == name or k.startswith(name + "{"))


def max_by_name(samples: dict[str, float], name: str) -> float:
    vals = [v for k, v in samples.items() if k == name or k.startswith(name + "{")]
    return max(vals) if vals else 0.0


def histogram_quantile(samples: dict[str, float], name: str, q: float) -> float:
    """Estimate a quantile from cumulative _bucket series, the way Prometheus
    does: find the bucket containing the rank, then interpolate linearly
    inside it. The answer is only as good as your bucket boundaries -- which
    is the honest cost of an aggregatable histogram, and it is worth paying.
    """
    buckets: list[tuple[float, float]] = []
    for key, value in samples.items():
        if not key.startswith(f"{name}_bucket{{"):
            continue
        m = re.search(r'le="([^"]+)"', key)
        if m:
            buckets.append((float(m.group(1)), value))
    if not buckets:
        return float("nan")
    buckets.sort()
    total = buckets[-1][1]
    if total <= 0:
        return 0.0
    target = q * total
    prev_le, prev_count = 0.0, 0.0
    for le, count in buckets:
        if count >= target:
            if le == float("inf"):
                return prev_le
            span = count - prev_count
            frac = 0.0 if span == 0 else (target - prev_count) / span
            return prev_le + (le - prev_le) * frac
        prev_le, prev_count = le, count
    return buckets[-1][0]


def proc_rss_kb(pid: int) -> float:
    try:
        with open(f"/proc/{pid}/status") as fh:
            for line in fh:
                if line.startswith("VmRSS:"):
                    return float(line.split()[1])
    except OSError:
        pass
    return 0.0


def proc_cpu_ticks(pid: int) -> float:
    try:
        with open(f"/proc/{pid}/stat") as fh:
            parts = fh.read().rsplit(")", 1)[1].split()
        return float(parts[11]) + float(parts[12])     # utime + stime
    except (OSError, IndexError):
        return 0.0


def find_pid(pattern: str) -> int | None:
    for entry in os.listdir("/proc"):
        if not entry.isdigit():
            continue
        try:
            with open(f"/proc/{entry}/cmdline", "rb") as fh:
                cmd = fh.read().replace(b"\x00", b" ").decode(errors="replace")
        except OSError:
            continue
        if pattern in cmd:
            return int(entry)
    return None


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("out", nargs="?", default="/tmp/pulse-metrics.csv")
    ap.add_argument("--url", default="http://localhost:8000/metrics")
    ap.add_argument("--pid", type=int, default=None, help="worker pid")
    ap.add_argument("--gen", default="k6", help="load generator process match")
    ap.add_argument("--baseline-mb", type=float, default=None,
                    help="worker RSS with zero connections, for kb_per_conn")
    ap.add_argument("--interval", type=float, default=1.0)
    args = ap.parse_args()

    pid = args.pid or find_pid("uvicorn pulse.asgi")
    if pid is None:
        sys.exit("no uvicorn worker found; pass --pid")
    gen_pid = find_pid(args.gen)

    baseline_mb = args.baseline_mb if args.baseline_mb is not None \
        else proc_rss_kb(pid) / 1024.0
    print(f"collecting pid={pid} gen={gen_pid} baseline={baseline_mb:.1f} MB "
          f"-> {args.out}", file=sys.stderr)

    fields = ["ts", "conns", "loop_lag_ms", "in_rate", "out_rate", "amp",
              "gs_p99_ms", "rss_mb", "kb_per_conn", "cpu_pct", "gen_cpu_pct"]

    prev = scrape(args.url)
    prev_t = time.time()
    prev_cpu = proc_cpu_ticks(pid)
    prev_gen_cpu = proc_cpu_ticks(gen_pid) if gen_pid else 0.0

    with open(args.out, "w", newline="") as fh:
        writer = csv.DictWriter(fh, fieldnames=fields)
        writer.writeheader()
        while True:
            time.sleep(args.interval)
            now = time.time()
            cur = scrape(args.url)
            dt = now - prev_t or 1.0

            conns = sum_by_name(cur, "chat_connections_active")
            in_rate = (sum_by_name(cur, "chat_messages_inbound_total")
                       - sum_by_name(prev, "chat_messages_inbound_total")) / dt
            out_rate = (sum_by_name(cur, "chat_messages_outbound_total")
                        - sum_by_name(prev, "chat_messages_outbound_total")) / dt
            cpu = proc_cpu_ticks(pid)
            gen_cpu = proc_cpu_ticks(gen_pid) if gen_pid else 0.0
            rss_mb = proc_rss_kb(pid) / 1024.0

            row = {
                "ts": int(now),
                "conns": int(conns),
                "loop_lag_ms": round(
                    max_by_name(cur, "chat_event_loop_lag_seconds") * 1000, 2),
                "in_rate": round(in_rate, 1),
                "out_rate": round(out_rate, 1),
                "amp": round(out_rate / in_rate, 1) if in_rate > 0 else 0,
                "gs_p99_ms": round(
                    histogram_quantile(cur, "chat_group_send_seconds", 0.99) * 1000, 2),
                "rss_mb": round(rss_mb, 1),
                "kb_per_conn": round((rss_mb - baseline_mb) * 1024 / conns, 1)
                if conns else 0,
                "cpu_pct": round((cpu - prev_cpu) / CLOCK_TICKS / dt * 100, 1),
                "gen_cpu_pct": round((gen_cpu - prev_gen_cpu) / CLOCK_TICKS / dt * 100, 1),
            }
            writer.writerow(row)
            fh.flush()
            print(f"conns={row['conns']:>6}  lag={row['loop_lag_ms']:>7} ms  "
                  f"out/s={row['out_rate']:>9}  amp={row['amp']:>5}  "
                  f"cpu={row['cpu_pct']:>5}%  gen={row['gen_cpu_pct']:>5}%",
                  file=sys.stderr)

            prev, prev_t, prev_cpu, prev_gen_cpu = cur, now, cpu, gen_cpu


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        pass
