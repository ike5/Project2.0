# Lab 11 — Move, Spawn, Tune

**You'll:** drive a player with input, spawn prefabs, and feed values from a
ScriptableObject. ⏱️ ~55 min. Continue in your `MiniGame` project from Module 10.

---

## Part A — Move the player
1. Add `Assets/Scripts/TransformMover.cs` (contents from
   [`unity-scripts/TransformMover.cs`](../unity-scripts/TransformMover.cs)).
2. Select your `Player` square → **Add Component → TransformMover**.
3. Press **Play**. Use **arrow keys / WASD** to move the square. Adjust **Speed** in
   the Inspector (during Play to feel it; re-set while stopped to keep it).

✅ Movement is smooth and frame-rate independent thanks to `Time.deltaTime`.

## Part B — Make a prefab to spawn
1. Create a new sprite: Hierarchy → right-click → **2D Object → Sprites → Circle**.
   Rename `Coin`, set a yellow color, scale to ~0.5.
2. Drag `Coin` from the **Hierarchy** into `Assets/` (make a `Prefabs` folder first).
   This creates a **prefab**. Delete the `Coin` from the Hierarchy (the prefab remains
   in the Project).

## Part C — Spawn prefabs at runtime
1. Create an empty: Hierarchy → **Create Empty**, rename `Spawner`.
2. Add `Assets/Scripts/Spawner.cs` ([source](../unity-scripts/Spawner.cs)) to it.
3. In the Inspector, drag the **Coin prefab** onto the script's **Prefab** field.
4. **Play**, press **Space** repeatedly — coins appear at random spots and auto-destroy
   after the lifetime. Tune **Range** and **Lifetime**.

✅ You instantiated prefabs and cleaned them up with `Destroy(clone, lifetime)`.

## Part D — Tune from a ScriptableObject
1. Add `Assets/Scripts/GameSettings.cs` ([source](../unity-scripts/GameSettings.cs)).
2. Create an asset: **Project → right-click → Create → MiniGame → Game Settings**.
   Name it `DefaultSettings`. Set `moveSpeed`, `coinValue`, etc. in its Inspector.
3. Make `TransformMover` read from it (small edit):
   ```csharp
   [SerializeField] private GameSettings settings;
   private void Update()
   {
       float speed = settings != null ? settings.moveSpeed : 5f;
       // ...use 'speed' as before...
   }
   ```
4. Drag `DefaultSettings` onto the Player's `TransformMover` **Settings** field. Change
   `moveSpeed` on the **asset** and watch every consumer pick it up.

✅ Data lives in an asset, decoupled from the scene — change once, affects all users.

## Part E — A coroutine (bonus)
Add to any script and call `StartCoroutine(Flash())` from `Start`:
```csharp
using System.Collections;
private IEnumerator Flash()
{
    for (int i = 0; i < 3; i++) { Debug.Log("flash " + i); yield return new WaitForSeconds(0.5f); }
}
```
✅ The logs appear half a second apart — work spread across frames, no threads.

## What you learned
- The MonoBehaviour lifecycle drives your code; `Update` + `Time.deltaTime` for motion.
- `Instantiate`/`Destroy` spawn and remove prefab instances at runtime.
- ScriptableObjects centralize tunable data as assets.
- Coroutines spread work over time — Unity's alternative to `async` for timing.

➡️ **[challenge.md](./challenge.md)** then [Module 12](../12-unity-2d-game/).
