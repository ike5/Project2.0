# Module 12 — Build a 2D Game

**Goal:** assemble a complete, playable **2D coin-collector**: a physics-driven player,
collectible coins with collisions, a score, and a win condition. ⏱️ ~3 h ·
🎯 Prereq: 10–11.

---

## What you'll build

A top-down arena: move a player square with the keyboard, collect spinning coins, and
win at N coins — with a live score HUD.

```
  ┌───────────────── Score: 30 ─────────────────┐
  │   ●           ◯                ◯             │
  │        ◻ player                              │
  │              ◯          ◯                    │
  └──────────────────────────────────────────────┘
```

## 1. 2D physics essentials

- **Rigidbody2D** — makes a GameObject move under the physics engine. Set **Gravity
  Scale = 0** for top-down (no falling).
- **Collider2D** (BoxCollider2D / CircleCollider2D) — the shape used for collisions.
- **Trigger vs collision:**
  - A normal collider **blocks** movement and fires `OnCollisionEnter2D`.
  - A collider with **Is Trigger = true** lets objects pass through and fires
    `OnTriggerEnter2D` — perfect for pickups.
- **Tags** — label GameObjects (e.g. `Player`) so scripts can identify what they hit
  (`other.CompareTag("Player")`).

## 2. Read input in `Update`, move in `FixedUpdate`

Physics runs on a fixed clock. Sample input every frame (`Update`), then apply movement
to the `Rigidbody2D` in `FixedUpdate` for stable collisions — exactly what
[`PlayerMovement2D`](../unity-scripts/2d/PlayerMovement2D.cs) does with
`_rb.MovePosition`.

## 3. Collect with triggers

[`Coin`](../unity-scripts/2d/Coin.cs) puts its collider in trigger mode; on
`OnTriggerEnter2D` with the player it reports to the `GameManager` and destroys itself.

## 4. Game state with a simple manager

[`GameManager`](../unity-scripts/2d/GameManager.cs) is a lightweight **singleton**
(`GameManager.Instance`) holding score and the win check. Coins call
`GameManager.Instance.AddScore(value)`. It updates the
[`HudController`](../unity-scripts/2d/HudController.cs), which drives **TextMeshPro**
on-screen text.

> The singleton pattern here is just the C# you know (a static `Instance` property)
> applied to a MonoBehaviour. Keep managers few and simple.

## 5. UI text with TextMeshPro

Unity's standard text is **TextMeshPro (TMP)**. The first time you add TMP text the
editor offers to import **"TMP Essentials"** — accept it. UI lives on a **Canvas**
(covered more in Module 13).

---

## Do the lab
Build the whole game step by step: arena, player, coin prefab, spawning, scoring, win.
👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Reference scripts
[`unity-scripts/2d/`](../unity-scripts/2d/): `PlayerMovement2D.cs`, `Coin.cs`,
`GameManager.cs`, `HudController.cs`.

## Key terms
Rigidbody2D · Collider2D · trigger vs collision · `OnTriggerEnter2D` · tags ·
`Update` vs `FixedUpdate` · singleton manager · TextMeshPro · Canvas

**Next →** [Module 13: 3D, Physics, UI & Audio](../13-unity-3d-ui-audio/)
