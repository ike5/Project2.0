# Lab 13 — Roll-a-Ball in 3D

**You'll:** build a 3D game with physics, a follow camera, UI, sound, and a second
scene. ⏱️ ~90 min. Create a new **3D (Built-In or URP)** project, or a 3D scene in your
existing project. Add scripts from [`unity-scripts/3d/`](../unity-scripts/3d/) and reuse
[`HudController`](../unity-scripts/2d/HudController.cs).

---

## Part A — Ground and player
1. Hierarchy → **3D Object → Plane**, rename `Ground`, scale to (2,1,2).
2. Hierarchy → **3D Object → Sphere**, rename `Player`, position (0, 0.5, 0).
   - Add **Rigidbody** (gravity on).
   - Add **BallController**. Set the **Tag** to **Player**.
3. **Play** → roll with WASD/arrows. Tune **Force**. The sphere falls onto the plane and
   rolls. Stop.

✅ 3D physics with `AddForce` in `FixedUpdate`.

## Part B — Follow camera
1. Create `Assets/Scripts/CameraFollow.cs`:
   ```csharp
   using UnityEngine;
   public class CameraFollow : MonoBehaviour
   {
       [SerializeField] private Transform target;
       [SerializeField] private Vector3 offset = new(0, 8, -8);
       private void LateUpdate()
       {
           if (target != null) transform.position = target.position + offset;
       }
   }
   ```
2. Select **Main Camera**, add **CameraFollow**, drag `Player` into **Target**. Angle the
   camera down toward the player.
3. **Play** → the camera trails the ball smoothly (it's in `LateUpdate`).

## Part C — Pickups
1. Hierarchy → **3D Object → Cube**, rename `Pickup`, scale ~0.5, position above the
   ground. Add a **material** (Project → Create → Material, set a color, drag onto cube).
2. On `Pickup`: check the **Collider**'s **Is Trigger**, add **PickUp3D**, and
   *(optional)* a **Rotator** (set it to spin around Y by editing the axis, or reuse Z).
3. Drag `Pickup` into `Assets/Prefabs/`. Place ~8 copies around the ground (or spawn
   them).

## Part D — HUD + manager
1. **UI → Text - TextMeshPro** for the score (`ScoreText`) and another for messages
   (`MessageText`). Create a `HUD` object with **HudController**, wire the texts.
2. Create empty `GameManager`, add **Game3DManager**, set **Count To Win = 8**, drag the
   `HUD` in.
3. **Play** → roll over pickups; the score rises; at 8 you see **"You Win!"**.

## Part E — Audio
1. Add an **AudioSource** to `GameManager`, assign a music clip, enable **Loop** (and
   **Play On Awake** or rely on `musicSource.Play()` in `Start`).
2. Put a short SFX clip on the **Pickup prefab**'s `PickUp3D` **Pickup Sound** field —
   `PlayClipAtPoint` plays it as each pickup is collected.
3. Ensure the **Main Camera** has an **AudioListener** (default). **Play** and listen.

> No audio files handy? Unity has none built in — grab free clips (e.g. from Unity Asset
> Store freebies) or skip audio; the game still works.

## Part F — A win scene + button
1. **File → Save As** a second scene `Win.unity`. Add a **UI → Button - TextMeshPro**
   ("Play Again") and a title text.
2. Create `MenuActions.cs`:
   ```csharp
   using UnityEngine;
   using UnityEngine.SceneManagement;
   public class MenuActions : MonoBehaviour
   {
       public void LoadGame() => SceneManager.LoadScene("Main");
   }
   ```
   Add it to an empty object, wire the Button's **OnClick** → `MenuActions.LoadGame`.
3. **File → Build Settings** → **Add Open Scenes** so both `Main` and `Win` are listed.
4. In `Game3DManager.Win()`, load the win scene:
   `UnityEngine.SceneManagement.SceneManager.LoadScene("Win");`
5. **Play** from `Main` → win → the `Win` scene loads → click **Play Again** → back to `Main`.

✅ A full 3D loop across two scenes with UI navigation.

## What you learned
- 3D Rigidbody physics, materials, and a `LateUpdate` follow camera.
- Canvas UI with TextMeshPro and a clickable Button wired to a method.
- AudioSource music + one-shot SFX.
- Multi-scene games via Build Settings + `SceneManager.LoadScene`.

➡️ **[challenge.md](./challenge.md)** then [Module 14](../14-build-and-ship/).
