# Solutions 15: Reference Capstone

The reference capstone is "Arena Survivors," a small roguelike built in 30 days. The full project is in `Reference/`. The deliverables, retrospective, and runbook are below.

## 1. The shipped game

**Arena Survivors** is a 2D roguelike. The player spawns in an arena, fights waves of enemies, picks up XP, levels up, and survives as long as possible. After 5 minutes, a boss spawns. Killing the boss ends the run.

**Platforms shipped:**
- iOS TestFlight (v1.0, v1.1, v1.2)
- Android Play Internal (v1.0, v1.1, v1.2)
- itch.io (v1.0, v1.1, v1.2)

**Downloads (first 30 days):**
- iOS: 412 (TestFlight external)
- Android: 1,847 (Play Internal)
- itch.io: 3,205

**Crash rate:** 0.4% (3 crashes in 750 sessions)

**Average session:** 6m 20s

**Day 1 retention:** 38%
**Day 7 retention:** 12%

## 2. The spec

`SPEC.md` (excerpt):
```
# Arena Survivors

A 2D roguelike. Survive 5 minutes, kill the boss, win.

## Core loop
1. Player spawns in arena with starting weapon (pistol).
2. Waves of enemies spawn from the edges. Difficulty increases over time.
3. Killing enemies drops XP gems.
4. XP fills a bar; at threshold, player levels up.
5. Level up offers 3 random upgrades. Pick one.
6. After 5 minutes, a boss spawns.
7. Killing the boss ends the run. Player sees final score.
8. Player returns to menu. New run is randomized.

## Win/lose
- Win: kill the boss. Score = time survived + enemies killed + level reached.
- Lose: player health reaches 0. Score = time survived + enemies killed + level reached.

## Controls
- WASD / left stick: move.
- Mouse / right stick: aim.
- Left click / A: shoot.

## Systems
- Player controller (input -> velocity).
- Camera follow.
- Weapon system (shoot, cooldown, damage, projectile).
- Enemy AI (Spawn, Chase, Attack, Die).
- Wave spawner (timed waves, escalating difficulty).
- XP and leveling.
- Upgrade system (5 upgrades, 3 random, pick one).
- Boss enemy (3 attack patterns).
- HUD (health, XP, timer, score, level).
- Game state (Menu, Playing, Paused, GameOver).
- Save/load (high score, settings, last run).
- Settings (audio, graphics, controls).
- Tutorial (first-time UX).

## Out of scope
- Multiplayer.
- Multiple weapons.
- Procedural levels.
- Localization.
- Mod support.
- Cloud saves.
```

## 3. The architecture

`ARCHITECTURE.md` (excerpt):
```
# Architecture

## System diagram

+-----------------------------------+
|  UI Layer (MonoBehaviour)         |
|  - HUD                            |
|  - Main Menu                      |
|  - Pause Menu                     |
|  - Game Over Screen               |
|  - Settings                       |
|  - Upgrade Selection              |
+----------------+------------------+
                 | (events)
                 v
+-----------------------------------+
|  Game Logic Layer (MonoBehaviour) |
|  - GameStateManager               |
|  - WaveService                    |
|  - EconomyService                 |
|  - UpgradeService                 |
+----------------+------------------+
                 |
                 v
+-----------------------------------+
|  Simulation Layer (MonoBehaviour) |
|  - PlayerController               |
|  - Enemy FSM                      |
|  - WeaponSystem                   |
|  - ProjectilePool                 |
|  - EnemyPool                      |
|  - VfxPool                        |
+----------------+------------------+
                 |
                 v
+-----------------------------------+
|  Data Layer (ScriptableObjects)   |
|  - EnemyConfigs                   |
|  - UpgradeConfigs                 |
|  - WaveConfig                     |
|  - DifficultyConfig               |
+-----------------------------------+

## Patterns in use

| Pattern | Where | Why |
|---------|-------|-----|
| Object pool | ProjectilePool, EnemyPool, VfxPool | Eliminate Instantiate/Destroy in hot path |
| State machine | Player, Enemy, Game | Discrete states, transitions |
| ScriptableObject | EnemyConfigs, UpgradeConfigs, WaveConfig | Data-driven design |
| Event bus | GameEvents | Cross-system communication |
| Async save/load | SaveSystem | Avoid main-thread hitches |
| DI container | GameLifetimeScope | Testable services |
| Object pooling | State machine pool | Zero-alloc transitions |

## DI graph

- GameStateManager (Singleton)
- WaveService (Singleton, depends on GameStateManager)
- EconomyService (Singleton, depends on SaveSystem)
- UpgradeService (Singleton)
- SaveSystem (Singleton, wrapped)
- GameEvents (Static, no DI)
- SettingsService (Singleton, depends on SaveSystem)
- GameBootstrap (EntryPoint, depends on GameStateManager)

## Data flow

- Player input -> PlayerController -> velocity.
- WaveService timer -> spawn enemy -> EnemyPool.
- Enemy dies -> drops XP gem -> Player picks up -> XP fills -> Level up -> UpgradeService.
- Game state transitions: Menu -> Playing -> Paused -> Playing -> GameOver.
- Save on GameOver -> SaveSystem.
```

## 4. The build pipeline

Module 13's pipeline, configured for Arena Survivors:

- `.github/workflows/pr.yml`: edit-mode tests + Android build. 5-7 minutes.
- `.github/workflows/main.yml`: full tests + all platform builds + size check. 15-20 minutes.
- `.github/workflows/nightly.yml`: full tests + 30-minute soak test. 45 minutes.
- `.github/workflows/release.yml`: on tag, build + fastlane submit. 30-40 minutes.

The pipeline is green on every commit. The size report shows:
- Android AAB: 28 MB (budget: 60 MB).
- iOS IPA: 32 MB (budget: 80 MB).
- Windows player: 45 MB (budget: 100 MB).

The size has not regressed. The pipeline caught 2 regressions (a 12 MB texture imported without compression, a 4 MB audio file that should have been streamed).

## 5. The hotfix pipeline

The team shipped 3 hotfixes in the first 30 days:

**v1.0.1 (Day 8)**: boss was invulnerable to one of its own attack patterns. 1-line fix. Hotfix in 3 hours.

**v1.0.2 (Day 12)**: save file corruption on Android if the app was killed during save. Added atomic write. 5-line fix. Hotfix in 4 hours.

**v1.1.0 (Day 20)**: difficulty curve was too aggressive. Adjusted spawn rate. 10-line config change. Shipped in 6 hours.

The hotfix capability was tested on day 7 with a synthetic bug. The team did a dry-run hotfix in 2 hours. The next day, when a real bug appeared, the fix took 3 hours.

## 6. The retrospective

`RETRO.md`:
```
# Arena Survivors Retrospective

## Project: Arena Survivors
## Duration: 30 days
## Team: 1 (solo senior dev)
## Shipped: v1.0 (Day 25), v1.0.1, v1.0.2, v1.1.0

## Metrics
- Downloads: 5,464 across all platforms
- Crash rate: 0.4%
- Average session: 6m 20s
- Day 1 retention: 38%
- Day 7 retention: 12%

## What went well

1. **CI/CD pipeline on day 3**. Saved probably 2 days of debugging build issues at the end.
2. **Hot reload for iteration**. The Hot Reload package saved 3-4 days of "save, wait, test" cycle time.
3. **Object pooling from day 1**. Zero performance issues with 100 enemies on screen.
4. **Async save/load**. Zero hitches on save. Players didn't notice saves were happening.
5. **The spec**. Locked the scope on day 1. No major scope creep. The game that shipped is the game that was specified.
6. **TestFlight submission on day 22**. Found the App Store Connect configuration issues early. Submission on day 24 was smooth.
7. **Crash reporting with symbols**. The 0.4% crash rate was debugged in 30 minutes because we had line numbers.

## What went wrong

1. **v1.0.0 had a save corruption bug**. The atomic write was missing. Discovered on day 12 when an Android tester reported it. Should have been caught on day 1.
2. **The first build was 60 MB on Android**. The AAB was 32 MB larger than the budget. Had to optimize textures, which took 1 day that wasn't allocated.
3. **The boss AI had a bug**. The boss was invulnerable to one of its own attacks. Took 1 day to find and fix. Should have been caught by the AI tests.
4. **Marketing on day 26 was too late**. The game shipped on day 25, but the marketing materials weren't ready until day 26. The first day of launch had no marketing.
5. **No telemetry for "player died at level X"**. The retention metrics are aggregate, not per-funnel. Hard to know where players are dropping off.

## What we learned

1. **TestFlight / Play Internal in week 3, not week 4**. The submission process has surprises. Find them early.
2. **Atomic file IO from day 1**. Save corruption is a critical bug. The fix is 5 lines. There's no excuse.
3. **The lowest-spec device is the test target**. The dev machine ran at 200 fps. The Pixel 4a ran at 22 fps. Profile on the slow device.
4. **Buffer days are not optional**. Day 27 was eaten by the v1.0.0 save corruption bug. Without buffer, the launch would have slipped by 2 days.
5. **The retrospective is the input**. Writing this document took 2 hours. The lessons will save 1-2 weeks on the next project.
6. **The hotfix capability is a senior's promise**. We shipped 3 hotfixes in 30 days. The players noticed. The retention held.

## What we'll do differently next time

1. **Lock the spec earlier**. Day 1, not day 3. The 2 days of "what should the game be" cost us 2 days at the end.
2. **Add a save corruption test**. Write a test that simulates a power loss during save. The test would have caught v1.0.0.
3. **Test on the lowest-spec device from day 1**. The Pixel 4a is the test target. Not the dev machine.
4. **Allocate 25% buffer, not 10%**. The 10% buffer was eaten by unexpected bugs. 25% would have given breathing room.
5. **Telemetry from day 1**. Per-funnel retention data. We didn't have it. The next project will.
6. **Marketing materials in week 3, not week 4**. The launch day should have marketing. The next project will.
7. **Write the retrospective in real-time**. I wrote this 7 days after launch. I should have written it as we went. The lessons are fresher.

## Final notes

The game shipped. The spec was met. The CI/CD pipeline worked. The crash rate is low. The retention is decent for a 30-day project.

The next project will be better. The retrospective is the input. The senior's job is to make the next one cheaper, faster, and more reliable.
```

## 7. The post-launch runbook

`RUNBOOK.md`:
```
# Post-Launch Runbook

## Triage process

1. **Collect**: every bug report goes to GitHub Issues.
2. **Categorize**: Crash, Gameplay, UI, Audio, Performance, Other.
3. **Prioritize**:
   - P0: crash, blocks gameplay. Fix in 24h.
   - P1: gameplay broken, has workaround. Fix in 1 week.
   - P2: minor, cosmetic. Fix in next release.
   - P3: nice-to-have. Backlog.
4. **Reproduce**: try to reproduce. If you can't, ask for more info.
5. **Fix**: P0 and P1 first. P2 and P3 in batches.
6. **Verify**: test on the lowest-spec device.
7. **Release**: build, submit, release notes.

## Hotfix process (P0)

1. Diagnose the bug. Find the line of code.
2. Fix it. The fix is a 1-10 line change.
3. Build for the affected platforms. ~30 minutes.
4. Run the smoke tests. ~30 minutes.
5. Submit to the store. ~30 minutes for the build, ~1-2 hours for review.
6. Release with release notes. ~30 minutes.
7. Total: 4-6 hours from bug to live.

## Build commands

### iOS TestFlight
```bash
fastlane ios beta
```

### Android Play Internal
```bash
fastlane android internal
```

### itch.io
```bash
./scripts/upload-itch.sh
```

## Crash reporting

- Firebase Crashlytics for iOS and Android.
- Sentry for the dedicated server (when added).
- Symbol upload is automatic via the release workflow.

## Metrics

- Crash rate (target: < 0.5%)
- Day 1 retention (target: > 30%)
- Day 7 retention (target: > 10%)
- Average session (target: > 5m)
- Store rating (target: > 4.0)

## On-call

Solo dev, no on-call rotation. The on-call is "me, when I see the alert." The triage process is the same.

## Release cadence

- Hotfixes: as needed for P0.
- Minor releases (v1.x): every 2 weeks.
- Major releases (v2.x): every 2-3 months.
```

## 8. The metrics

The 30-day metrics for Arena Survivors:

| Metric | Target | Actual | Status |
|--------|--------|--------|--------|
| Crash rate | < 0.5% | 0.4% | pass |
| Day 1 retention | > 30% | 38% | pass |
| Day 7 retention | > 10% | 12% | pass |
| Average session | > 5m | 6m 20s | pass |
| Store rating | > 4.0 | 4.3 | pass |
| Android AAB size | < 60 MB | 28 MB | pass |
| iOS IPA size | < 80 MB | 32 MB | pass |
| Build time (PR) | < 10m | 7m | pass |
| Build time (main) | < 25m | 18m | pass |
| Hotfix time | < 6h | 3-4h | pass |

The metrics are the senior's feedback loop. The retrospective is the input. The next project is the output.

## 9. The shipped build

The shipped build is the deliverable. The build is on TestFlight, Play Internal, and itch.io. Players can download it. Players can play it. Players can leave reviews. The senior's job is done.

The next project starts on day 31. The retrospective is written. The runbook is in place. The pipeline is automated. The senior is ready.
