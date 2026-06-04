# Module 13 — 3D, Physics, UI & Audio

**Goal:** step into the third dimension — 3D objects, rigidbody physics, a camera that
follows, proper UI on a Canvas, audio, and moving between scenes. ⏱️ ~3 h ·
🎯 Prereq: 10–12.

---

## 1. 3D vs 2D — what changes

- A third axis: **Y is up**, movement is usually on the **X/Z plane**.
- **Rigidbody** (not Rigidbody2D), **Collider** (BoxCollider/SphereCollider/MeshCollider),
  `OnTriggerEnter` / `OnCollisionEnter` (no `2D` suffix).
- **Materials** color/texture 3D meshes (vs Sprite Renderer in 2D).
- You think about a **camera** position/angle in 3D space.

The *concepts* are identical — only the dimensionality and component names change.

## 2. Rigidbody physics with forces

```csharp
[RequireComponent(typeof(Rigidbody))]
public class BallController : MonoBehaviour
{
    private Rigidbody _rb;
    void Awake() => _rb = GetComponent<Rigidbody>();
    void FixedUpdate() => _rb.AddForce(input.normalized * force);   // physics in FixedUpdate
}
```
`AddForce` pushes the body; gravity and collisions are handled by the engine. See
[`unity-scripts/3d/BallController.cs`](../unity-scripts/3d/BallController.cs).

## 3. Camera follow

A simple follow keeps an **offset** from the target each frame:
```csharp
void LateUpdate() => transform.position = target.position + offset;   // after movement
```
Use **`LateUpdate`** for cameras so the target has already moved this frame (no jitter).

## 4. UI on a Canvas

Unity UI lives on a **Canvas** (a `Canvas` + `EventSystem` are auto-created with your
first UI element). Common pieces:
- **TextMeshPro** text (score, messages) — Module 12.
- **Button** — wire its **OnClick** to a public method (e.g. restart, start).
- **Panel/Image** — backgrounds, menus.
- The **Canvas Scaler** keeps UI sized across resolutions ("Scale With Screen Size").

Buttons call methods you expose:
```csharp
public void OnRestartClicked() => SceneManager.LoadScene(0);
```
Drag the GameObject onto the Button's **OnClick (+)** and pick the method.

## 5. Audio

- An **AudioSource** plays an **AudioClip**. Background music = an AudioSource with
  **Play On Awake** + **Loop**.
- One-shot SFX: `AudioSource.PlayClipAtPoint(clip, position)` or
  `source.PlayOneShot(clip)`.
- An **AudioListener** (on the Main Camera by default) is the "ears" — keep exactly one.

## 6. Scenes & transitions

Split your game into **Scenes** (menu, level 1, win screen). Add them to **File → Build
Settings → Scenes In Build**, then switch:
```csharp
using UnityEngine.SceneManagement;
SceneManager.LoadScene("Level2");      // by name (must be in Build Settings)
SceneManager.LoadScene(0);             // by build index
```
Persist data across scenes via a `DontDestroyOnLoad` manager or `PlayerPrefs`/a
ScriptableObject.

---

## Do the lab
Build a 3D "roll-a-ball": a physics sphere, pickups, a follow camera, a HUD, sound, and
a win screen scene. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Reference scripts
[`unity-scripts/3d/`](../unity-scripts/3d/): `BallController.cs`, `PickUp3D.cs`,
`Game3DManager.cs` (HUD reuses `unity-scripts/2d/HudController.cs`).

## Key terms
3D Rigidbody/Collider · `AddForce` · `OnTriggerEnter` · Material · camera follow ·
`LateUpdate` · Canvas/EventSystem · Button OnClick · AudioSource/AudioClip/AudioListener ·
`SceneManager.LoadScene` · Build Settings · `DontDestroyOnLoad`

**Next →** [Module 14: Build & Ship (Capstone B)](../14-build-and-ship/)
