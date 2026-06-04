# Unity Reference Scripts

The C# scripts used across the Unity modules (10–14). Because a full Unity project is
binary/`.meta`-heavy, this course ships **just the scripts** plus precise editor
instructions in each module's `lab.md` — you create the project in Unity Hub and add
these scripts to `Assets/Scripts/`.

> ⚠️ **Unity rule:** a script file's name **must match its class name** (e.g.
> `PlayerMovement2D.cs` contains `class PlayerMovement2D`). Keep them in sync when you
> copy them in.

## Contents
| File | Module | Purpose |
|------|--------|---------|
| `HelloUnity.cs` | 10 | First script: `Start`/`Update`, `[SerializeField]`, `Debug.Log` |
| `TransformMover.cs` | 11 | Move via Transform + input + `Time.deltaTime` |
| `Spawner.cs` | 11 | `Instantiate`/`Destroy` a prefab |
| `GameSettings.cs` | 11 | A `ScriptableObject` data asset |
| `2d/PlayerMovement2D.cs` | 12 | Rigidbody2D movement (Update input / FixedUpdate physics) |
| `2d/Coin.cs` | 12 | Trigger pickup → score |
| `2d/GameManager.cs` | 12 | Score/win singleton |
| `2d/HudController.cs` | 12–13 | TextMeshPro HUD (score/message/timer) |
| `3d/BallController.cs` | 13 | 3D Rigidbody `AddForce` movement |
| `3d/PickUp3D.cs` | 13 | 3D trigger pickup + SFX |
| `3d/Game3DManager.cs` | 13 | 3D score/win + audio |

These can't be compiled outside Unity (they reference `UnityEngine`); they're verified
against the Unity 6 API and exercised via the labs in-editor.
