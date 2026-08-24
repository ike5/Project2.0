/**
 * apps/pulse-web/src/lib/protocol.ts
 *
 * TypeScript types for the Pulse wire protocol v1. The NORMATIVE definition is
 * `05-protocol-and-domain-design/code/pulse-protocol-v1.md`; this file is a
 * transcription. If the two disagree, that file is right and this one is a bug.
 *
 * Two rules from §1 shape every type here, and they are asymmetric on purpose:
 *
 *   * Clients MUST ignore unknown `type` values -> `Envelope["type"]` is a
 *     union PLUS `string`, and every switch has a `default:` that returns.
 *   * Clients MUST ignore unknown keys inside `data` -> no exhaustive object
 *     types on inbound frames, and never `Object.keys(data).length === n`.
 *
 * "Strict about what you accept from a client you do not control, liberal about
 * what you accept from a server you do." The client is the liberal half.
 */

// ---------------------------------------------------------------------------
// §1 The envelope
// ---------------------------------------------------------------------------

export interface Envelope<T = Record<string, unknown>> {
  /** Protocol major version. Absent means 1. */
  v?: number;
  /** §3. Unknown values MUST be ignored. Hence `| (string & {})`. */
  type: WireType | (string & {});
  /** `room.<slug>` — Room.key. Equal to `chat_message.room_id` in the store. */
  room: string;
  /**
   * Epoch MILLISECONDS, SERVER clock.
   *
   * §1: "Clients MUST NOT use their own clock for display or ordering." A
   * client whose clock is 40 seconds fast renders tomorrow's timestamps; one
   * that sorts by local arrival time reorders history on a slow network. Sort
   * by `seq`, display `ts`.
   */
  ts: number;
  data: T;
}

export type WireType =
  // §3.1 messages
  | 'message.create' | 'message.ack' | 'message.new'
  | 'message.edit'   | 'message.update'
  | 'message.delete' | 'message.removed'
  // §3.2 presence and typing
  | 'presence.update' | 'typing.start' | 'typing.update'
  // §3.3 read state
  | 'read.upto' | 'read.update'
  // §3.4 heartbeat
  | 'ping' | 'pong'
  // §3.5 resume
  | 'resume' | 'resume.batch'
  // §3.6 control, §4 errors
  | 'control' | 'error'
  // Module 17's v1-compatible multiplexing extension. §1: "Adding an optional
  // `data` key, or a new `type`, is a COMPATIBLE change." No `v` bump.
  | 'room.subscribe' | 'room.unsubscribe' | 'room.subscribed';

// ---------------------------------------------------------------------------
// §2 Identity — three identifiers, never interchangeable
// ---------------------------------------------------------------------------

/** Client-generated, before the FIRST send attempt. Unique per (room, client_id). */
export type ClientId = string;
/** Server-generated at persist time. Snowflake (Module 12). int64 -> number is
 *  UNSAFE past 2^53; see the note in room-store.ts. */
export type MessageId = number;
/** Server, per room, GAPLESS, monotonic. The ordering and resume cursor. */
export type Seq = number;

// ---------------------------------------------------------------------------
// §3 Frame payloads (inbound ones are intentionally non-exhaustive)
// ---------------------------------------------------------------------------

export interface MessageCreate {
  client_id: ClientId;
  body: string;                 // 1–4096 chars after strip
  reply_to?: MessageId;
}

export interface MessageAck {
  client_id: ClientId;
  id: MessageId;
  seq: Seq;
  /** True when the server recognized a retry and returned the ORIGINAL ids. */
  duplicate: boolean;
}

export interface MessageNew {
  id: MessageId;
  seq: Seq;
  /** Echoed so the SENDER can recognize its own optimistic bubble (§3.1). */
  client_id: ClientId;
  sender: string;
  body: string;
  reply_to?: MessageId | null;
}

export interface ResumeRequest {
  /** "I have everything up to and including this." */
  from_seq: Seq;
}

export interface ResumeBatch {
  messages: MessageNew[];
  from_seq: Seq;
  /**
   * NOT "the seq of the last message in this batch". It is "this batch covers
   * everything up to and INCLUDING to_seq".
   *
   * On has_more === false the client sets its cursor to `to_seq`, NOT to
   * messages.at(-1).seq. That single line is the entire permanent-gap
   * mechanism: it steps the client over a hole the server has confirmed will
   * never fill (a dead-lettered poison message, or a seq allocated by a
   * process that died before publishing).
   *
   * A client that advances to the last message's seq re-requests the same hole
   * forever, and Module 11's rl:resume limiter (5 burst, 0.1/s) then freezes
   * the room.
   */
  to_seq: Seq;
  has_more: boolean;
}

export interface PresenceUpdate {
  user: string;
  state: 'join' | 'leave';
  online: string[];
}

export interface TypingUpdate {
  /** Aggregated server-side, at most 1 frame per room per second (§3.2). */
  users: string[];
}

export interface ReadUpdate {
  user: string;
  seq: Seq;
}

// §3.6
export type ControlAction = 'drain' | 'reauth' | 'revoked' | 'rate_limited';

export interface ControlFrame {
  action: ControlAction | (string & {});
  reason?: string;
  retry_after_ms?: number;
}

// ---------------------------------------------------------------------------
// §4 Errors
// ---------------------------------------------------------------------------

export type ErrorCode =
  | 'bad_frame' | 'unknown_type' | 'unsupported_version'
  | 'unexpected_fields' | 'missing_fields'
  | 'empty_body' | 'body_too_long' | 'bad_client_id'
  | 'rate_limited' | 'not_a_member';

export interface ErrorFrame {
  code: ErrorCode | (string & {});
  /** For humans. MAY change between releases -- never branch on it. */
  message: string;
  retry_after_ms?: number;
  /** Present whenever the offending frame carried one, so a client with
   *  several messages in flight can mark the RIGHT bubble. */
  client_id?: ClientId;
  [k: string]: unknown;         // §1: ignore unknown keys, do not reject them
}

/**
 * §4: "An `error` frame MUST NOT close the connection."
 *
 * This table is the client's half of that contract. `retry` means "resend the
 * SAME frame with the SAME client_id after retry_after_ms"; anything else is a
 * bug on one side or the other and retrying makes it worse.
 */
export const ERROR_POLICY: Record<string, 'bug' | 'user' | 'retry' | 'stop'> = {
  bad_frame: 'bug',
  unknown_type: 'bug',
  unexpected_fields: 'bug',
  missing_fields: 'bug',
  unsupported_version: 'stop',   // downgrade or prompt the user to update
  empty_body: 'user',
  body_too_long: 'user',
  bad_client_id: 'user',
  rate_limited: 'retry',         // the ONLY retryable code
  not_a_member: 'stop',          // the socket will close with 4403
};

// ---------------------------------------------------------------------------
// §4 Close codes — NOT the same numbers as the STOMP course. Do not guess.
// ---------------------------------------------------------------------------

export const CLOSE = {
  NORMAL: 1000,
  GOING_AWAY: 1001,
  ABNORMAL: 1006,               // no frame received; the network died
  TOO_LARGE_TRANSPORT: 1009,
  SLOW_CONSUMER: 4008,          // YOUR fault: shed work before reconnecting
  TOO_LARGE_APP: 4009,
  UNAUTHENTICATED: 4401,        // mint a NEW ticket, then reconnect
  FORBIDDEN: 4403,              // do not reconnect for this room
  ABUSE: 4429,                  // long backoff (Module 21)
} as const;

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

/** §1: `room` is always the COMPOSED key. Never send a bare slug. */
export const roomKey = (slug: string): string => `room.${slug}`;
export const roomSlug = (key: string): string => key.replace(/^room\./, '');

export function envelope<T>(type: WireType, room: string, data: T): Envelope<T> {
  // Note the absence of `ts`. §1 says `ts` is the SERVER clock; a client that
  // stamps its own is asserting something it cannot know. The server fills it.
  return { v: 1, type, room, ts: 0, data };
}
