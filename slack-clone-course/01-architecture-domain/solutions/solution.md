# Challenge 01 — Reference Solution

Run `SET search_path TO explore;` first.

### 1. Members of Acme, ordered by role
```sql
SELECT u.username, m.role
FROM membership m
JOIN app_user u  ON u.id = m.user_id
JOIN workspace w ON w.id = m.workspace_id
WHERE w.slug = 'acme'
ORDER BY CASE m.role WHEN 'owner' THEN 0 WHEN 'admin' THEN 1 ELSE 2 END, u.username;
```
Result: `ann (owner)`, then `bob`, `cat` (members).

### 2. DM participants
```sql
SELECT u.username
FROM channel_member cm
JOIN app_user u ON u.id = cm.user_id
WHERE cm.channel_id = 4;
```
Result: `ann`, `bob`.

### 3. Busiest channel
```sql
SELECT COALESCE(c.name, '(dm)') AS channel, COUNT(m.id) AS msgs
FROM channel c
LEFT JOIN message m ON m.channel_id = c.id
GROUP BY c.id, c.name
ORDER BY msgs DESC;
```
Result: `#general` and the `(dm)` are tied at 3; `#random`/`#founders` have 0.

### 4. A reaction table
```sql
CREATE TABLE reaction (
    id         serial PRIMARY KEY,
    message_id int  REFERENCES message(id),
    user_id    int  REFERENCES app_user(id),
    emoji      text NOT NULL,
    UNIQUE (message_id, user_id, emoji)   -- one user, one emoji, once per message
);
```
> The uniqueness constraint is the **triple** `(message_id, user_id, emoji)`: the
> same user *may* add different emoji to a message, and different users may add the
> same emoji, but a given (user, emoji) pair is allowed only once per message.

### 5. Why DMs-as-channels simplifies Module 05
> Because a DM is just a `channel`, the WebSocket consumer, the message table, and
> the broadcast-to-a-group logic are identical for channels and DMs — you write one
> code path instead of two. The only difference is how the channel was created
> (`kind='dm'`, no name), not how messages flow through it.
