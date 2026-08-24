"""
apps/pulse/chat/resume.py — the server half of protocol §3.5.

  resume        C→S   { from_seq }
  resume.batch  S→C   { messages, from_seq, to_seq, has_more }

Four rules this file exists to enforce, none of which are optional:

  1. BOUNDED BATCHES. A client gone for a week must not be able to make you
     stream 400,000 rows over a socket. MAX_BATCH caps it and `has_more` tells
     the client to ask again.

  2. AN ABANDON THRESHOLD. Past ABANDON_THRESHOLD messages behind, paging over
     the socket is the wrong transport entirely. Tell the client to drop its
     cursor and page history through the DRF CursorPagination endpoint
     (Module 12), which is keyset and stays flat at any depth.

  3. `to_seq` IS NOT "the last message's seq". It is "this batch covers
     everything up to and including to_seq". On a complete batch the client
     advances its cursor to to_seq, which steps it over any permanent hole — a
     sequence number that was allocated but whose entry was dead-lettered. This
     is the entire permanent-gap mechanism and it needs no protocol change.

  4. CLAMP THE INPUT. from_seq arrives from a client you do not control. A
     negative value, a value above the room's maximum, or a missing value must
     all produce a cheap query, not an unbounded one.

Reads use `connection.cursor()` rather than the ORM: this is a hot path (a mass
reconnect is thousands of these per second) and Module 12 measured the ORM's
per-row instantiation cost. The room/user objects around it stay ORM.
"""

from __future__ import annotations

from dataclasses import dataclass, field

from channels.db import database_sync_to_async
from django.db import connection
from prometheus_client import Counter, Histogram

MAX_BATCH = 200
ABANDON_THRESHOLD = 5_000

_resume_requests = Counter(
    "pulse_resume_requests_total", "resume frames handled", ["outcome"]
)
_resume_depth = Histogram(
    "pulse_resume_depth_messages",
    "how far behind the client was",
    buckets=(1, 10, 50, 200, 1000, 5000, 20000, 100000),
)
_resume_latency = Histogram("pulse_resume_seconds", "resume query latency")


@dataclass
class ResumeResult:
    messages: list[dict] = field(default_factory=list)
    from_seq: int = 0
    to_seq: int = 0
    has_more: bool = False
    abandon: bool = False

    def as_data(self) -> dict:
        """The `data` object of a resume.batch envelope."""
        data = {
            "messages": self.messages,
            "from_seq": self.from_seq,
            "to_seq": self.to_seq,
            "has_more": self.has_more,
        }
        if self.abandon:
            # Additive optional key — a compatible change under protocol §1.
            # Clients that predate it simply keep paging, which is correct if
            # slower, so this cannot break anyone.
            data["abandon"] = True
        return data


# Ordered by seq, which is the table's primary key prefix in Module 12's schema
# (PRIMARY KEY (room_id, seq)), so this is a primary-key range scan: no sort, no
# extra index, and it stays a range scan after Module 13 partitions the table.
_SQL = """
    SELECT m.id, m.seq, m.client_id, u.username AS sender, m.body,
           m.reply_to_id,
           (extract(epoch FROM m.created_at) * 1000)::bigint AS ts
      FROM chat_message m
      JOIN chat_room r ON r.id = m.room_id
      JOIN auth_user  u ON u.id = m.sender_id
     WHERE r.slug = %s
       AND m.seq > %s
       AND m.deleted_at IS NULL
     ORDER BY m.seq
     LIMIT %s
"""

_MAX_SQL = """
    SELECT coalesce(max(m.seq), 0)
      FROM chat_message m JOIN chat_room r ON r.id = m.room_id
     WHERE r.slug = %s
"""


@database_sync_to_async
def resume(room_key: str, from_seq: int) -> ResumeResult:
    """
    `room_key` is the composed key — "room.general" — the same string that is the
    channel-layer group name, the protocol's `room` field, and the store's room
    identity. `Room.slug` is the bare handle; strip the prefix for the query.
    """
    slug = room_key.removeprefix("room.")

    with _resume_latency.time():
        with connection.cursor() as cur:
            cur.execute(_MAX_SQL, [slug])
            current_max = int(cur.fetchone()[0])

            # RULE 4 — clamp. A hostile client sending from_seq=-1 would
            # otherwise make `seq > -1` scan the entire room. A client sending
            # from_seq far above current_max gets an empty batch, not an error:
            # it is what happens legitimately when a client's cursor survives a
            # room reset.
            from_seq = max(0, min(int(from_seq), current_max))

            behind = current_max - from_seq
            _resume_depth.observe(behind)

            # RULE 2 — abandon.
            if behind > ABANDON_THRESHOLD:
                _resume_requests.labels(outcome="abandon").inc()
                return ResumeResult(
                    from_seq=from_seq, to_seq=current_max, has_more=False, abandon=True
                )

            # RULE 1 — bounded. LIMIT MAX_BATCH + 1 is the standard has_more
            # trick: fetch one extra row, and its presence tells you there is
            # more without a second COUNT query.
            cur.execute(_SQL, [slug, from_seq, MAX_BATCH + 1])
            rows = cur.fetchall()

    has_more = len(rows) > MAX_BATCH
    rows = rows[:MAX_BATCH]

    messages = [
        {
            "id": r[0],
            "seq": r[1],
            "client_id": r[2],
            "sender": r[3],
            "body": r[4],
            "reply_to": r[5],
            "ts": r[6],
        }
        for r in rows
    ]

    # RULE 3 — to_seq semantics.
    #   has_more  → the batch ends at the last row we actually returned.
    #   complete  → the batch covers everything the room has, INCLUDING any
    #               sequence numbers that will never be filled.
    if has_more:
        to_seq = messages[-1]["seq"]
    else:
        to_seq = current_max

    _resume_requests.labels(outcome="batch").inc()
    return ResumeResult(
        messages=messages, from_seq=from_seq, to_seq=to_seq, has_more=has_more
    )


@database_sync_to_async
def mark_read(room_key: str, user_id: int, seq: int) -> int:
    """
    read.upto (protocol §3.3). A high-water mark, not a per-message receipt.

    GREATEST() makes this idempotent AND order-independent: a duplicated or
    out-of-order receipt can never move the cursor backwards. That property is
    what lets receipts ride at-most-once transport (Module 09's routing rule) —
    a lost receipt is repaired by the next one, for free.
    """
    slug = room_key.removeprefix("room.")
    with connection.cursor() as cur:
        cur.execute(
            """
            INSERT INTO chat_readcursor (room_id, user_id, last_read_seq, updated_at)
            SELECT r.id, %s, %s, now() FROM chat_room r WHERE r.slug = %s
            ON CONFLICT (room_id, user_id) DO UPDATE
               SET last_read_seq = GREATEST(chat_readcursor.last_read_seq,
                                            EXCLUDED.last_read_seq),
                   updated_at = now()
            RETURNING last_read_seq
            """,
            [user_id, int(seq), slug],
        )
        return int(cur.fetchone()[0])


@database_sync_to_async
def unread_summary(room_key: str, user_id: int) -> dict:
    """
    Unread is a subtraction, never a stored counter.

    A maintained counter drifts, because incrementing it and inserting the
    message are two writes that are not atomic across a crash. Two integers
    cannot drift.
    """
    slug = room_key.removeprefix("room.")
    with connection.cursor() as cur:
        cur.execute(
            """
            SELECT
              coalesce((SELECT max(m.seq) FROM chat_message m
                         WHERE m.room_id = r.id), 0)                AS room_seq,
              coalesce((SELECT c.last_read_seq FROM chat_readcursor c
                         WHERE c.room_id = r.id AND c.user_id = %s), 0) AS read_seq
              FROM chat_room r WHERE r.slug = %s
            """,
            [user_id, slug],
        )
        room_seq, read_seq = cur.fetchone()
    return {
        "room": room_key,
        "room_seq": room_seq,
        "read_seq": read_seq,
        "unread": max(0, room_seq - read_seq),
    }
