# Lab 15: Plan and Start the Capstone

**Time**: 90 minutes
**Goal**: Write the spec, set up the architecture, configure the CI/CD pipeline, and start the first week of the capstone. By the end of the lab, you have a playable prototype skeleton and a working build pipeline.

## Setup (10 min)

1. Create a new Unity 6 project. Name it `[YourGameName]`.
2. Initialize a git repo. Push to a private GitHub repo.
3. Create a folder structure: `Assets/Scripts/Config/`, `Assets/Scripts/Combat/`, `Assets/Scripts/UI/`, `Assets/Scripts/State/`, `Assets/Scenes/`, `Assets/Prefabs/`, `Assets/Configs/`, `Assets/Art/`, `Assets/Audio/`.
4. Install the packages you need: `com.unity.addressables` (only if you need it), `com.unity.memoryprofiler`, `com.unity.test-framework`, `com.unity.collections`, `com.unity.entities` (only if you need ECS).

## Part A: Write the spec (20 min)

A 1-3 page document. Use the template from the README. Include:

- The game concept (one paragraph).
- The core loop (5-7 steps).
- Win/lose conditions.
- Controls.
- Systems (the systems you need to build).
- Out of scope (what you're explicitly not building).

Save it as `SPEC.md` in the repo root. Commit it. This is the contract.

## Part B: Architecture document (15 min)

Write `ARCHITECTURE.md`:
- System diagram.
- Pattern usage table (from module 14).
- The DI container graph.
- The data flow.

The senior's architecture document is 1-2 pages. Bullet points, not prose. The next developer reads it in 5 minutes and understands the system.

## Part C: CI/CD pipeline (25 min)

Reuse the pipeline from module 13:
- `.github/workflows/pr.yml`: edit-mode tests + Android build.
- `.github/workflows/main.yml`: full tests + all platform builds.
- `.github/workflows/nightly.yml`: full tests + soak test.
- `.github/workflows/release.yml`: on tag, submit to TestFlight + Play Internal.

Copy the `BuildScript.cs` from module 13. Modify the scenes list, the bundle ID, the application name.

Get the pipeline green. Push a trivial change. Watch the build run. Verify the artifact.

## Part D: Player controller (10 min)

The simplest possible player controller. The senior's first version is the version that compiles.

`Assets/Scripts/Player/PlayerController.cs`:
```csharp
using UnityEngine;

[RequireComponent(typeof(Rigidbody2D))]
public class PlayerController : MonoBehaviour
{
    [SerializeField] float moveSpeed = 5f;

    Rigidbody2D _rb;

    void Awake() => _rb = GetComponent<Rigidbody2D>();

    void Update()
    {
        var move = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
        _rb.linearVelocity = move * moveSpeed;
    }
}
```

Add a Rigidbody2D, a SpriteRenderer, a Collider2D. Make a `Player` prefab. Place it in a `Main` scene.

## Part E: Camera follow (5 min)

`Assets/Scripts/Player/CameraFollow.cs`:
```csharp
using UnityEngine;

public class CameraFollow : MonoBehaviour
{
    [SerializeField] Transform target;
    [SerializeField] float smoothSpeed = 5f;

    void LateUpdate()
    {
        if (target == null) return;
        var targetPos = new Vector3(target.position.x, target.position.y, transform.position.z);
        transform.position = Vector3.Lerp(transform.position, targetPos, smoothSpeed * Time.deltaTime);
    }
}
```

Add to the main camera. Drag the player in.

## Part F: First commit and verify (5 min)

1. Commit: `feat: player controller and camera follow`.
2. Push. Verify the CI runs.
3. Open the `Main` scene in the editor. Press Play. Move the player with WASD. Camera follows.

The first week of the capstone is the skeleton. The senior's rule: get something compiling and running, then iterate. Don't try to build the whole game in week 1.

## Verification

1. The spec is written, committed, and concrete.
2. The architecture document is written and references the patterns from module 14.
3. The CI pipeline is green on a trivial change.
4. The player controller works: WASD moves the player, camera follows.
5. The build artifact is downloadable from the Actions tab.

## Common pitfalls

- **Spec too vague**: "make a fun game" is not a spec. "Roguelike, 5-minute runs, 3 upgrades per level, 1 boss at the end" is a spec.
- **Architecture document too long**: a 20-page document doesn't get read. A 2-page document does.
- **Pipeline not set up in week 1**: if you don't have the pipeline by day 3, you'll spend the last week fixing build issues.
- **Player controller over-engineered**: you don't need state, you don't need DI, you don't need a config. You need a Rigidbody2D and Input.GetAxisRaw. The senior writes the simple version first.
- **Camera not following**: you forgot to assign the target. Or you used `Update` instead of `LateUpdate` and the camera jitters.
- **Push to main triggers a broken build**: the pipeline is green on a trivial change. Make sure the build script works before you push real code.
- **No build report**: you built the project but didn't write a build report. Add it.

## What we're testing

- Can you write a spec that is concrete and bounded?
- Can you write an architecture document that is short and clear?
- Can you set up a CI pipeline from scratch in 25 minutes?
- Can you build the simplest possible player controller and commit it?
- Do you understand the milestone plan and the scope?

## Stretch goals

- Add an enemy that follows the player.
- Add a projectile that the player can fire.
- Add a health bar.
- Add a game over screen.
- Add a wave spawner.

Each stretch goal is a 30-60 minute task. The senior's week 1 is "skeleton that compiles, plus one feature." If you have time for more, add more. If not, that's fine.

## The 30-day plan

| Day | Task | Deliverable |
|-----|------|-------------|
| 1 | Spec, architecture, CI setup | `SPEC.md`, `ARCHITECTURE.md`, green pipeline |
| 2 | Player controller, camera, scene | Playable player in scene |
| 3 | Enemy spawner, basic AI | Enemies spawn and chase |
| 4 | Combat (shoot, damage, die) | Enemies die when shot |
| 5 | First playable prototype | Game loop runs end-to-end |
| 6 | Wave system | Timed spawns, difficulty curve |
| 7 | XP and leveling | XP bar fills, level up |
| 8 | Upgrade system | 3 random upgrades, pick one |
| 9 | Boss enemy | Boss spawns, boss AI |
| 10 | HUD | Health, XP, timer, score |
| 11 | Game state machine | Menu, playing, paused, game over |
| 12 | Save/load | High score persists |
| 13 | Settings menu | Audio, graphics settings |
| 14 | Main menu | Title, new game, continue |
| 15 | Tutorial | First-time UX |
| 16 | Juice | Screen shake, particles, hitstop |
| 17 | UI art pass | Polish the UI |
| 18 | Audio pass | Music, SFX |
| 19 | Tutorial polish | First-time UX |
| 20 | Bug bash | Fix worst bugs |
| 21 | Performance pass | 60 fps on target device |
| 22 | Platform-specific fixes | TestFlight / Play Internal |
| 23 | Store assets | Screenshots, descriptions, icon |
| 24 | Submit to TestFlight | Build available to internal testers |
| 25 | Submit to Play Internal | Build available to internal testers |
| 26 | Marketing | Twitter, TikTok, devlog |
| 27 | Buffer | For unexpected issues |
| 28 | Final build | All platforms |
| 29 | Buffer | |
| 30 | Retrospective, post-launch setup | Document the run |

The plan is the plan. The senior adjusts as needed, but the milestones are the checkpoints. If you're behind on day 15, cut scope. If you're ahead on day 10, add polish. The plan is the tool, not the master.
