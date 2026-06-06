-- A throwaway exploration schema for Module 01. This is NOT the real schema —
-- Django will generate that in Module 02. We hand-write it here only to make the
-- relationships tangible and queryable. Load it into a scratch database:
--
--   docker compose -f ../../00-setup/compose.dev.yml exec -T postgres \
--     psql -U slack -d slack < code/seed.sql

DROP SCHEMA IF EXISTS explore CASCADE;
CREATE SCHEMA explore;
SET search_path TO explore;

CREATE TABLE app_user (
    id       serial PRIMARY KEY,
    username text UNIQUE NOT NULL,
    email    text UNIQUE NOT NULL
);

CREATE TABLE workspace (
    id    serial PRIMARY KEY,
    name  text NOT NULL,
    slug  text UNIQUE NOT NULL
);

CREATE TABLE membership (
    id           serial PRIMARY KEY,
    user_id      int REFERENCES app_user(id),
    workspace_id int REFERENCES workspace(id),
    role         text NOT NULL DEFAULT 'member',  -- owner | admin | member
    UNIQUE (user_id, workspace_id)
);

CREATE TABLE channel (
    id           serial PRIMARY KEY,
    workspace_id int REFERENCES workspace(id),
    name         text,                            -- null for DMs
    kind         text NOT NULL DEFAULT 'public',  -- public | private | dm
    UNIQUE (workspace_id, name)
);

CREATE TABLE channel_member (   -- who's in a private/DM channel
    channel_id int REFERENCES channel(id),
    user_id    int REFERENCES app_user(id),
    last_read  int DEFAULT 0,                      -- id of last message they've seen
    PRIMARY KEY (channel_id, user_id)
);

CREATE TABLE message (
    id         serial PRIMARY KEY,
    channel_id int REFERENCES channel(id),
    author_id  int REFERENCES app_user(id),
    parent_id  int REFERENCES message(id),         -- thread reply → its parent
    body       text NOT NULL,
    created_at timestamptz NOT NULL DEFAULT now()
);

-- ── Seed data ────────────────────────────────────────────────────────────────
INSERT INTO app_user (username, email) VALUES
  ('ann', 'ann@example.com'),
  ('bob', 'bob@example.com'),
  ('cat', 'cat@example.com');

INSERT INTO workspace (name, slug) VALUES ('Acme', 'acme');

INSERT INTO membership (user_id, workspace_id, role) VALUES
  (1, 1, 'owner'), (2, 1, 'member'), (3, 1, 'member');

INSERT INTO channel (workspace_id, name, kind) VALUES
  (1, 'general', 'public'),
  (1, 'random',  'public'),
  (1, 'founders','private'),
  (1, NULL,      'dm');           -- a DM between ann and bob

INSERT INTO channel_member (channel_id, user_id, last_read) VALUES
  (3, 1, 0), (3, 2, 0),           -- ann + bob in #founders
  (4, 1, 2), (4, 2, 1);           -- ann + bob DM; ann read up to msg 2, bob to msg 1

INSERT INTO message (channel_id, author_id, parent_id, body) VALUES
  (1, 1, NULL, 'Welcome to Acme! 👋'),
  (1, 2, NULL, 'Hi everyone'),
  (1, 3, 2,    'hey bob, glad you joined'),   -- a thread reply to message 2
  (4, 1, NULL, 'bob, got a sec?'),
  (4, 2, NULL, 'sure, what''s up'),
  (4, 1, NULL, 'sent you the doc');
