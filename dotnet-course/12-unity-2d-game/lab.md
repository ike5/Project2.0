# Lab 12 — The Coin-Collector Game

**You'll:** build a complete, playable 2D game. ⏱️ ~90 min. Continue in `MiniGame`,
or make a fresh **Universal 2D** project. Add all scripts from
[`unity-scripts/2d/`](../unity-scripts/2d/) into `Assets/Scripts/`.

> Tip: keep the **Console** visible — script errors show there and block Play.

---

## Part A — The player (physics movement)
1. Hierarchy → **2D Object → Sprites → Square**, rename `Player`, center at (0,0,0).
2. Add components to `Player`:
   - **Rigidbody2D** → set **Gravity Scale = 0** (top-down).
   - **BoxCollider2D** (leave as a solid collider).
   - **PlayerMovement2D** (your script).
3. At the top of the Inspector, set the **Tag** dropdown to **Player** (Add Tag… if
   needed, then assign).
4. **Play** → move with WASD/arrows. Tune **Speed**. Stop.

✅ Physics-driven movement via `Rigidbody2D.MovePosition` in `FixedUpdate`.

## Part B — The coin prefab (a trigger)
1. Hierarchy → **2D Object → Sprites → Circle**, rename `Coin`, color it yellow, scale ~0.5.
2. Add to `Coin`:
   - **CircleCollider2D** → check **Is Trigger**.
   - **Coin** (your script).
   - *(optional)* **Rotator** from Module 11 so it spins.
3. Drag `Coin` into `Assets/Prefabs/` to make a **prefab**. Delete the scene copy.

## Part C — The HUD (TextMeshPro)
1. Hierarchy → **UI → Text - TextMeshPro**. Accept **Import TMP Essentials** if asked.
   This creates a **Canvas** with a text object. Rename the text `ScoreText`, place it
   top-left, set text to `Score: 0`.
2. Add a second **UI → Text - TextMeshPro**, rename `MessageText`, center it, clear its
   text, make the font large.
3. Create an empty `HUD` GameObject, add **HudController**, and drag `ScoreText` →
   **Score Text**, `MessageText` → **Message Text**.

## Part D — The game manager
1. Hierarchy → **Create Empty**, rename `GameManager`. Add the **GameManager** script.
2. Set **Coins To Win** (e.g. 5). Drag the `HUD` object onto the **Hud** field.

## Part E — Spawn coins
Use the Module 11 `Spawner`:
1. Create empty `Spawner`, add **Spawner**, drag the **Coin prefab** into its Prefab
   field. Set a sensible **Range** to fit your view; set **Lifetime** high (e.g. 999) so
   coins persist until collected.
2. *(Or)* place 5 coin instances by hand for a fixed level.

## Part F — Play the game!
1. **Play**. Move the player into coins — each pickup:
   - logs nothing per frame (good), increments **Score** in the HUD,
   - removes the coin (trigger + `Destroy`).
2. Collect `Coins To Win` coins → the Console logs **"You win!"** and `MessageText`
   shows **"You Win!"**.

✅ A complete loop: input → physics → collision → score → win. That's a game.

## Part G — Polish (pick a couple)
- Add the **Rotator** to the coin prefab so coins spin.
- Add walls: create elongated squares with `BoxCollider2D` (not triggers) so the player
  is contained.
- Add a **pickup sound** (preview of Module 13): add an `AudioSource` to the Coin and
  `AudioSource.PlayClipAtPoint(clip, transform.position)` before `Destroy`.

## What you learned
- Rigidbody2D + colliders; trigger vs solid collisions; tags.
- A score/win **GameManager** singleton driving a **TextMeshPro** HUD.
- Prefabs + spawning to populate a level.
- You shipped a playable 2D game.

➡️ **[challenge.md](./challenge.md)** then [Module 13](../13-unity-3d-ui-audio/).
