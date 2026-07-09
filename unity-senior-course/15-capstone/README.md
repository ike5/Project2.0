# Module 15: Capstone - Ship a Small Production-Grade Game

This module is the final exam. The deliverable is a small but production-grade game, shipped to at least one store, with a working CI/CD pipeline, a build report, a retrospective, and the post-launch triage workflow. By the end of the course you have shipped a real product, not a tutorial project.

## 1. The capstone scope

A small but complete game. Not a vertical slice. Not a tech demo. A real product that someone can download, install, and play.

The reference scope: a small roguelike or tower defense. ~30 days of work for a senior developer working solo. ~10 days for a small team. The deliverable is a TestFlight build (iOS), a Play Internal build (Android), and a Steam or itch.io build (PC).

**Why this scope?**

- A vertical slice is too small. It doesn't have the operational reality of a shipped game (build pipeline, store submission, post-launch triage).
- A full game is too big. It doesn't ship in 30 days.
- The 30-day scope is the right size for a senior to deliver a real product while learning the senior workflow.

**What "30 days" means in practice:**

- Days 1-5: architecture, scope lock, design doc, CI/CD setup.
- Days 6-15: core gameplay (player controller, enemy AI, combat, level).
- Days 16-20: meta systems (save/load, settings, menus, shop).
- Days 21-25: polish (UI art, audio, juice, tutorial).
- Days 26-28: store submission prep (screenshots, descriptions, privacy, ratings).
- Days 29-30: TestFlight / Play Internal release, retrospective, post-launch triage setup.

**What to skip:**

- Multiplayer. Multiplayer adds 3x the complexity. Single-player only.
- Procedural generation. Hand-crafted levels are faster to ship.
- Custom asset pipeline. Use Unity's defaults.
- Multiple game modes. One mode, polished.
- Localization. English only, with hardcoded strings.
- Mod support. Not in scope.
- Cloud saves. Local saves only.

**What to ship:**

- A complete game loop: start, play, win/lose, return to menu.
- Save/load that works.
- Settings that work (audio, graphics).
- A tutorial or onboarding.
- At least 3 levels of content.
- 30 minutes of gameplay.
- A credits screen.

## 2. The spec

A spec is a 1-3 page document that describes the game. The senior's spec is not a wishlist. It is a contract.

**Reference spec (excerpt):**

```
# Arena Survivors

A small roguelike. The player spawns in a small arena, fights waves of enemies, picks up XP, levels up, and survives as long as possible. After death, the run ends. New run is randomized.

## Core loop
1. Player spawns in arena with starting weapon.
2. Waves of enemies spawn from the edges.
3. Killing enemies drops XP.
4. XP fills a bar; at threshold, player levels up.
5. Level up offers 3 random upgrades.
6. Player picks one. Game continues.
7. After 5 minutes, a boss spawns. Killing the boss ends the run.
8. Player sees final score. Returns to menu.

## Win/lose
- Win: kill the boss. Score = time survived + enemies killed + level reached.
- Lose: player health reaches 0.

## Controls
- Left stick / WASD: move.
- Right stick / mouse: aim.
- A / left click: shoot.

## Systems
- Player controller (input -> velocity).
- Weapon system (shoot, cooldown, damage, projectile).
- Enemy AI (chase, attack).
- Wave spawner (timed waves, escalating difficulty).
- XP and leveling.
- Upgrade system (3 random, pick one).
- HUD (health, XP bar, timer, score).
- Game state (menu, playing, paused, game over).
- Save/load (high score, settings).

## Out of scope
- Multiplayer.
- Multiple weapons (one weapon, upgrades modify it).
- Procedural levels (one arena).
- Localization.
```

The spec is the contract. When you finish a feature, check it against the spec. If the spec doesn't mention it, you don't build it.

## 3. The milestone plan

30 days. The milestones are the checkpoints that keep you honest.

**Week 1: Foundations**
- Day 1: Project setup, version control, CI/CD pipeline (module 13).
- Day 2: Architecture document, pattern selection (module 14).
- Day 3: Player controller, camera, basic scene.
- Day 4: Enemy spawner, basic enemy AI.
- Day 5: Combat (player shoots, enemy takes damage, dies). End of week: playable prototype with one enemy type, one weapon, one arena.

**Week 2: Core gameplay**
- Day 6: Wave system (timed spawns, difficulty curve).
- Day 7: XP and leveling.
- Day 8: Upgrade system.
- Day 9: Boss enemy.
- Day 10: HUD (health, XP, timer, score).

End of week: complete gameplay loop from start to boss kill. No polish.

**Week 3: Meta systems**
- Day 11: Game state machine (menu, playing, paused, game over).
- Day 12: Save/load (high score, settings).
- Day 13: Settings menu (audio, graphics).
- Day 14: Main menu, game over screen.
- Day 15: Tutorial / first-time UX.

End of week: full game loop with menus.

**Week 4: Polish and ship**
- Day 16: Juice (screen shake, particles, hitstop, sound effects).
- Day 17: UI art pass.
- Day 18: Audio pass (music, SFX).
- Day 19: Tutorial polish, first-time UX.
- Day 20: Bug bash, fix the worst bugs.
- Day 21: Performance pass (module 12).
- Day 22: Platform-specific fixes (module 11). TestFlight / Play Internal.
- Day 23: Store assets (screenshots, descriptions, icon).
- Day 24: Submission to TestFlight / Play Internal.
- Day 25: Submission to Steam / itch.io.
- Day 26: Marketing (Twitter, TikTok, devlog).
- Day 27: Buffer day for unexpected issues.
- Day 28: Final build, retrospective.
- Day 29: Buffer.
- Day 30: Post-launch triage setup, doc the runbook.

The buffer days are not optional. The bug you didn't anticipate will eat them. The senior allocates buffer explicitly.

## 4. The architecture

Use the patterns from module 14. The reference architecture:

- **State machine**: player (Alive, Dead), enemy (Spawning, Chasing, Attacking, Dying), game (Menu, Playing, Paused, GameOver).
- **Object pool**: enemies, projectiles, particles, XP gems.
- **ScriptableObject configs**: enemy types, weapon types, upgrade types, level config.
- **Command pattern**: not needed for this scope. The game has no undo/redo. Skip it.
- **Event bus**: game events (enemy killed, XP gained, level up, game over).
- **DI container**: VContainer. Two scopes: bootstrap scope and game scope.
- **Async save/load**: high score, settings. Auto-save on game over.
- **Hybrid ECS**: not needed for this scope. The simulation is small (max 50 enemies on screen). MonoBehaviour is fast enough.
- **Addressables**: not needed for this scope. All assets in Resources. Addressables for a 30-day project is over-engineering.

The architecture is the simplest that solves the problem. Don't reach for ECS, don't reach for Addressables, don't reach for the command pattern. The senior rule: pick the right tool, not the most powerful tool.

## 5. The build pipeline

Module 13's pipeline. Specifically:

- GitHub Actions on every commit: edit-mode tests, build for Android.
- GitHub Actions on main: full test suite, all platforms, size check, symbol upload.
- Nightly: full test suite, soak test, profile capture.
- Release: TestFlight upload, Play Internal upload.

The pipeline must work by day 3. If you build the pipeline late, you spend the last week fixing build issues instead of polishing the game.

## 6. Going from 0 to a TestFlight build

The senior workflow for the first store submission:

**Day 22:**
1. Create the App Store Connect entry. Fill in the name, bundle ID, primary language, category.
2. Create the TestFlight internal testing group. Add yourself.
3. Build the iOS .ipa. Archive in Xcode. Upload to App Store Connect.
4. Wait for processing. Apple says "Ready to Test" in 5-30 minutes.
5. Install on your device. Test the full game.

**Common first-time issues:**

- Missing icons. App Store Connect requires a 1024x1024 icon and various device-specific sizes. Use `AppIconStudio` or generate them.
- Missing privacy manifest. Add `Assets/Plugins/iOS/PrivacyInfo.xcprivacy` (module 11).
- Wrong bundle ID. Match the App Store Connect entry.
- Wrong signing certificate. The first build needs a Development certificate; TestFlight upload needs a Distribution certificate.
- Wrong provisioning profile. Use `fastlane match` or manual provisioning.

**Day 23:**
1. Take 5-10 screenshots. Use Unity's `ScreenCapture.CaptureScreenshot` or Xcode's Devices window.
2. Write the App Store description. 4000 characters max, 170 character subtitle, 30 character promotional text.
3. Set the age rating, the privacy practices, the content rights.
4. Submit for TestFlight review. Apple approves internal builds automatically (no review). External testing requires review.

**Day 24-25:**
1. Same workflow for Play Internal. Build the AAB. Upload to Play Console. Wait for processing. Install on device.
2. Same workflow for Steam or itch.io. Build the Windows player. Upload.

By day 25 you have three builds available to external testers.

## 7. The post-launch triage workflow

After launch, you will get bug reports. The triage workflow is the system for handling them.

**The sources of bug reports:**

- TestFlight / Play Console / Steam crash reports (with symbols uploaded, you have line numbers).
- User reviews (1-star reviews on the store).
- Discord / Twitter / Reddit mentions.
- Your own playtesting.

**The triage process:**

1. **Collect**: every bug report goes into a single tracker (GitHub Issues, Linear, Jira).
2. **Categorize**: Crash, Gameplay, UI, Audio, Performance, Other.
3. **Prioritize**: P0 (crash, blocks gameplay), P1 (gameplay broken, has workaround), P2 (minor, cosmetic), P3 (nice-to-have).
4. **Reproduce**: try to reproduce. If you can't, ask for more info. If you can, file the steps.
5. **Fix**: P0 and P1 first. P2 and P3 in batches.
6. **Verify**: test the fix on the lowest-spec device (module 11).
7. **Release**: build, submit, wait for review, release.

**The hotfix pipeline:**

The senior maintains a "we can ship a hotfix in 4 hours" capability. The steps:

1. Diagnose the bug. Find the line of code.
2. Fix it. The fix is a 1-10 line change.
3. Build for the affected platforms. ~30 minutes.
4. Run the smoke tests. ~30 minutes.
5. Submit to the store. ~30 minutes for the build, ~1-2 hours for review.
6. Release. Announce.

Total: 4-6 hours from "I see the bug" to "the fix is live." This is the senior's promise to the players.

**The post-launch retrospective:**

After 7 days, write a retrospective. The format:

```
## What went well
- ...
- ...

## What went wrong
- ...
- ...

## What we learned
- ...
- ...

## What we'll do differently next time
- ...
- ...
```

The retrospective is the most valuable document you write. It is the input to the next project.

## 8. The retrospective template

```
# Capstone Retrospective

## Project: [name]
## Duration: [X] days
## Team: [size]

## Shipped
- iOS TestFlight build (v1.0)
- Android Play Internal build (v1.0)
- Steam / itch.io build (v1.0)

## Metrics
- Downloads: N
- Crash rate: 0.X%
- Average session: Xm
- Day 1 retention: X%
- Day 7 retention: X%

## What went well
- CI/CD pipeline from day 3. Saved [time].
- Hot reload for iteration. Saved [time].
- Object pooling from day 1. Zero perf issues.
- Async save/load. Zero hitches on save.

## What went wrong
- TestFlight submission took [time] because of [reason].
- The boss AI had a bug that crashed the game. Took [time] to fix.
- The first build had [N] crashes due to [reason].
- Scope creep. We added [feature] that took [time] and should have been cut.

## What we learned
- TestFlight / Play Internal submission needs [preparation].
- The lowest-spec device is the test target. Not the dev machine.
- Buffer days are not optional.
- The post-launch triage process is the difference between "we can fix bugs" and "we can't."

## What we'll do differently
- Lock scope in writing on day 1. No scope changes after day 5.
- Test on the lowest-spec device from day 1, not day 20.
- Build the CI/CD pipeline in week 1, not week 4.
- Allocate 20% buffer in the schedule, not 10%.
- Write the retrospective in real-time, not at the end.
```

## 9. The senior rules

1. Lock the spec on day 1. No scope changes after the first week.
2. Build the pipeline early. The pipeline is a product.
3. Test on the lowest-spec device from day 1.
4. Profile from day 1. Not when something is slow.
5. Pool the hot path. Don't pool everything.
6. Async save/load. Don't block the main thread.
7. Use the patterns from module 14. Don't reinvent them.
8. Submit to TestFlight / Play Internal in week 3, not week 4. Find the submission issues early.
9. Maintain the hotfix pipeline. The team that can ship a fix in 4 hours is the team that retains players.
10. Write the retrospective. The retrospective is the input to the next project.

## 10. Common pitfalls

- **Scope creep**: you add a feature that wasn't in the spec. The feature takes 3 days. The schedule slips. The senior rule: if it's not in the spec, it doesn't ship.
- **Late CI/CD**: you build the pipeline in week 4. The build takes 4 hours. You can't iterate. Build the pipeline in week 1.
- **Testing on the dev machine only**: the dev machine is fast. The lowest-spec device is slow. Test on the slow one.
- **Skipping the buffer**: the schedule has 30 days, you allocate 28 days of work. The 2 missing days are eaten by the bug you didn't anticipate.
- **No crash reporting**: you ship without crash reporting. You don't know what's crashing. The senior rule: crash reporting is a feature, ship it on day 1.
- **No symbol upload**: you have crash reports but no symbols. The stack traces are hex addresses. You can't fix what you can't see.
- **Marketing on launch day**: you submit the build, then tweet about it. The build isn't approved yet. The senior rule: prepare the marketing materials in week 4, post on launch day +1.
- **No retrospective**: you ship, you celebrate, you start the next project. The lessons are lost. The senior rule: write the retrospective within 7 days of launch.

## 11. The grading rubric

The capstone is graded on:

- **Shipped to at least one store (30%)**: the build is live, players can download it.
- **CI/CD pipeline works (15%)**: from `git push` to build artifact is automated.
- **Build report (10%)**: size, time, errors tracked over time.
- **Performance on target device (15%)**: 60 fps on the lowest-spec target.
- **Architecture (15%)**: uses the senior patterns appropriately.
- **Retrospective (10%)**: written within 7 days, honest, actionable.
- **Hotfix capability (5%)**: a 1-line bug fix can be deployed in < 4 hours.

A "shipped" capstone is a passing capstone. An "unshipped but architected" capstone is a failing capstone. The senior's job is to ship.

## What to read next

This is the last module. You have the foundation. The next step is your project, your team, your game. Ship it.

If you want to go deeper:
- The Unity docs are the source of truth.
- The Unity Forum and Unity Discord are the senior community.
- The book "Game Programming Patterns" by Robert Nystrom.
- The book "Crafting Interpreters" if you want to write a scripting system.
- The book "Designing Data-Intensive Applications" if you want to scale your backend.
- The book "The Pragmatic Programmer" for the engineering discipline.

Ship the game. Learn from the players. Write the retrospective. Start the next one.
