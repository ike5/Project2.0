# Capstone B — Self-Assessment Rubric

Score your finished game honestly. Aim for "Solid" or better across the board.

| Capability | Needs work | Solid | Mastery |
|------------|-----------|-------|---------|
| **Scripting** | copies snippets | writes MonoBehaviours confidently | clean components, correct lifecycle use, no per-frame waste |
| **Physics** | objects move | Rigidbody + colliders/triggers correct | input in Update / forces in FixedUpdate, stable collisions |
| **Game state** | globals everywhere | a manager tracks score/win/lose | clear flow, minimal singletons, ScriptableObject tuning |
| **UI** | text on screen | Canvas + TMP + working buttons | scales across resolutions, clean menu/HUD/pause |
| **Audio** | none | SFX + music | mixer/volume, no listener conflicts |
| **Scenes** | one scene | menu → game → win flow | data persists across scenes correctly |
| **Build** | runs in editor only | exports a runnable `.app` | knows Mono/IL2CPP, dev vs release, build settings |
| **Project hygiene** | messy `Assets/` | organized folders + `.gitignore` | reusable prefabs, sensible naming, documented README |
| **C# transfer** | Unity-only thinking | applies Phase 0 C# (LINQ, events, generics) | explains Unity-vs-.NET differences fluently |

**You've reached the goal when** you can open the Unity editor, build a small mechanic
from scratch, and export a playable build — and separately, take an unfamiliar .NET app
and support it. Two complementary skill sets, one language: **C#**.

### Where this leads
- **Now:** keep making small games; each one teaches more than a tutorial.
- **App support → dev:** your debugging/logging/EF/API skills are a launchpad into
  .NET development roles and tools/editor scripting (also C#).
- **Deeper game dev:** Input System, animation, pooling, Netcode, the Asset Store.
