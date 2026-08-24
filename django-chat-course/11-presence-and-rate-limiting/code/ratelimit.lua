-- apps/pulse/chat/lua/ratelimit.lua
--
-- Token bucket, atomic, with server-sourced time.
--
--   KEYS[1] = bucket key (hash: tokens, ts)
--   ARGV[1] = capacity          (max burst)
--   ARGV[2] = refill per second (sustained rate)
--   ARGV[3] = cost              (usually 1; resume costs more)
--
--   returns {allowed, retry_after_ms, tokens_left_x1000}
--
-- Two differences from the version in cheatsheets/redis.md, both deliberate:
--
-- 1. TIME COMES FROM REDIS, NOT FROM THE CALLER.
--    The cheatsheet passes now_ms as an argument, which is fine on one box. With
--    8 worker processes on 3 machines it is not: a machine whose clock is 200 ms
--    fast hands out 200 ms × refill_rate of free tokens on every call, forever,
--    and a machine that is slow starves its users. `redis.call('TIME')` gives
--    every caller the same clock by construction. (Redis 5+ replicates script
--    EFFECTS, not the script itself, so a non-deterministic script is legal —
--    on Redis 3.x this exact code would have been rejected.)
--
-- 2. IT RETURNS THE REMAINING TOKENS.
--    So the consumer can expose `pulse_ratelimit_tokens` and you can see a tier
--    approaching saturation before it starts denying. A limiter you cannot
--    observe is a limiter you will tune by guessing.
--
-- The PEXPIRE is what keeps this from being a memory leak. An idle bucket
-- refills to capacity after `capacity / rate` seconds, at which point its stored
-- state is indistinguishable from "absent" — so let it expire and be recreated.
-- Without it you accumulate one hash per user per room forever.

local now = redis.call('TIME')
local now_ms = tonumber(now[1]) * 1000 + math.floor(tonumber(now[2]) / 1000)

local cap  = tonumber(ARGV[1])
local rate = tonumber(ARGV[2])
local cost = tonumber(ARGV[3])

local b      = redis.call('HMGET', KEYS[1], 'tokens', 'ts')
local tokens = tonumber(b[1])
local ts     = tonumber(b[2])

if tokens == nil then
    tokens = cap          -- first sight of this key: a full bucket
    ts = now_ms
end

-- Refill. Clamped at capacity, so an idle bucket cannot bank credit.
local elapsed_ms = math.max(0, now_ms - ts)
tokens = math.min(cap, tokens + (elapsed_ms / 1000.0) * rate)

local ttl_ms = math.ceil(cap / rate * 1000) + 1000

if tokens < cost then
    -- Deny. Persist the refill so the next call does not recompute from a stale
    -- ts, and tell the caller exactly how long to wait — a client that guesses
    -- either wastes requests or waits too long.
    redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now_ms)
    redis.call('PEXPIRE', KEYS[1], ttl_ms)
    local retry_after_ms = math.ceil((cost - tokens) / rate * 1000)
    return {0, retry_after_ms, math.floor(tokens * 1000)}
end

tokens = tokens - cost
redis.call('HSET', KEYS[1], 'tokens', tokens, 'ts', now_ms)
redis.call('PEXPIRE', KEYS[1], ttl_ms)
return {1, 0, math.floor(tokens * 1000)}
