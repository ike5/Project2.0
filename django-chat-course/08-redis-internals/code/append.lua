-- append.lua -- allocate a per-room sequence number and append to the room's
-- stream, atomically, in one round trip.
--
-- This is the script Module 09's Streams fan-out is built on and the reason
-- Module 18's Redis Cluster migration is a config change instead of a rewrite.
-- Read the KEYS contract before you touch it.
--
--   KEYS[1] = room:{<slug>}:seq       the gapless per-room counter (Module 05)
--   KEYS[2] = room:{<slug>}:stream    the append-only log      (Module 09)
--
--   ARGV[1] = maxlen                  approximate trim target
--   ARGV[2] = client_id               idempotency key (Module 05)
--   ARGV[3] = sender
--   ARGV[4] = body
--   ARGV[5] = ts (epoch ms, server clock)
--
--   returns { seq, entry_id }
--
-- THE HASH TAG IS THE POINT.
--
-- Redis Cluster hashes only the text between the first '{' and the next '}'.
-- `room:{7}:seq` and `room:{7}:stream` therefore land in the SAME slot, on the
-- same node, and this script is legal in Cluster. Without the braces they hash
-- to different slots and Redis answers:
--
--     (error) CROSSSLOT Keys in request don't hash to the same slot
--
-- On a single Redis the braces do nothing at all. That is exactly why you put
-- them in now: the day you need them, changing every key name in a running
-- system is a migration, and adding them today is free.
--
-- The tag content is the ROOM, because the room is the entity every multi-key
-- operation in this system groups on. Tagging by anything else -- by user, by
-- node, by a random ticket value -- puts related keys on unrelated shards.
-- Module 18 finds exactly one place in the whole course where a later module
-- tagged by the wrong entity, and it is a good lesson in how quietly that
-- mistake waits.
--
-- Three rules this file obeys, and you should too:
--   1. Every key the script touches is declared in KEYS. Never build a key
--      name inside the script -- Cluster must know the slots statically.
--   2. The script is deterministic and bounded. No loops over unbounded
--      input, no randomness, no TIME-derived writes (replicas replay the
--      effects, but keeping scripts deterministic keeps them debuggable).
--   3. It is short. A slow script blocks EVERY client; `lua-time-limit` only
--      makes Redis start answering -BUSY, and SCRIPT KILL refuses once the
--      script has written.

local seq_key    = KEYS[1]
local stream_key = KEYS[2]

local maxlen    = tonumber(ARGV[1])
local client_id = ARGV[2]
local sender    = ARGV[3]
local body      = ARGV[4]
local ts        = ARGV[5]

-- Atomic because nothing else runs between these two calls. In application
-- code this is a check-then-act race; here it is free, and the freeness comes
-- from the single-threaded execution model, not from clever locking.
local seq = redis.call('INCR', seq_key)

-- MAXLEN with '~' trims whole macro-nodes only. Exact trimming walks and
-- removes individual entries -- O(n) work on the single thread, on EVERY
-- append. Module 08's Part D is about what O(n) commands do to a chat p99.
local entry_id = redis.call(
    'XADD', stream_key,
    'MAXLEN', '~', maxlen,
    '*',
    'seq',       seq,
    'client_id', client_id,
    'sender',    sender,
    'body',      body,
    'ts',        ts)

return { seq, entry_id }
