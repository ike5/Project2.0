# Challenge 15: Ship the Capstone

**Time**: 30 days (or as much as you can in 7-14 days if this is a class project)
**Goal**: Ship a small but production-grade game. TestFlight build (iOS), Play Internal build (Android), Steam/itch.io build (PC), CI/CD pipeline, build report, retrospective, post-launch triage setup.

## Scope

A small roguelike or tower defense. ~30 days of work for a senior. The deliverable is a real product that someone can download, install, and play.

## Requirements

### 1. Spec and architecture (Day 1-2)

- `SPEC.md`: 1-3 pages. Game concept, core loop, win/lose, controls, systems, out of scope.
- `ARCHITECTURE.md`: 1-2 pages. System diagram, pattern usage, DI graph, data flow.

### 2. CI/CD pipeline (Day 3)

- GitHub Actions on every PR: edit-mode tests + Android build.
- GitHub Actions on main: full tests + all platform builds + size check.
- Nightly: full tests + soak test.
- Release: TestFlight + Play Internal submission via fastlane.
- Build report generated on every build, tracked over time.

### 3. Core gameplay (Day 4-15)

- Player controller with state.
- Camera follow.
- Enemy AI (state machine, at least 3 states).
- Combat (projectile, damage, death).
- Wave spawner (timed waves, escalating difficulty).
- XP and leveling.
- Upgrade system (at least 5 upgrades).
- Boss enemy.
- HUD (health, XP, timer, score).

### 4. Meta systems (Day 16-20)

- Game state machine (menu, playing, paused, game over).
- Save/load (high score, settings, last run).
- Settings menu (audio, graphics).
- Main menu with new game / continue.
- Game over screen with retry / main menu.
- Tutorial / first-time UX.

### 5. Polish (Day 21-25)

- Juice: screen shake, particles, hitstop, sound effects, music.
- UI art pass: replace placeholder with real assets (or polished procedural art).
- Audio pass: SFX for actions, music for states.
- Tutorial polish: smooth first-time UX.
- Performance pass: 60 fps on the lowest-spec target device.
- Platform-specific fixes: IL2CPP stripping, build size, addressables if needed.

### 6. Store submission (Day 22-25)

- TestFlight: App Store Connect entry, internal testing group, build uploaded.
- Play Internal: Play Console entry, internal testing track, AAB uploaded.
- Steam or itch.io: store page, build uploaded.
- Store assets: 5-10 screenshots, description, icon, age rating, privacy practices.

### 7. Post-launch (Day 26-30)

- Crash reporting: symbol upload, dashboard, alert on regression.
- Triage process: bug tracker, categories, priorities, hotfix pipeline.
- Marketing: Twitter, TikTok, devlog, Reddit post.
- Retrospective: what went well, what went wrong, what we learned, what we'll do differently.

## Deliverables

1. The Unity 6 project, buildable and runnable.
2. `SPEC.md`, `ARCHITECTURE.md`, `BUILD.md`, `CICD.md`, `RELEASE.md`.
3. TestFlight build (iOS).
4. Play Internal build (Android).
5. Steam or itch.io build (PC).
6. The retrospective (`RETRO.md`).
7. The post-launch runbook (`RUNBOOK.md`).
8. A short video (5 minutes) showing the game in action.

## Acceptance criteria

| Criterion | Pass |
|-----------|------|
| Spec written and concrete | required |
| Architecture document written | required |
| CI/CD pipeline green on every commit | required |
| Game playable end-to-end | required |
| Win condition reachable | required |
| Lose condition reachable | required |
| Save/load works | required |
| 60 fps on target device | required |
| TestFlight build uploaded | required |
| Play Internal build uploaded | required |
| Steam/itch.io build uploaded | required |
| Crash reporting configured | required |
| Symbol upload working | required |
| Retrospective written within 7 days of launch | required |
| Hotfix capability demonstrated | required |

## Grading rubric

- **Shipped to at least one store (30%)**: the build is live, players can download it.
- **CI/CD pipeline works (15%)**: from `git push` to build artifact is automated.
- **Build report and size tracking (10%)**: documented over time.
- **Performance on target device (15%)**: 60 fps on the lowest-spec target.
- **Architecture (15%)**: senior patterns from module 14 used appropriately.
- **Retrospective and runbook (10%)**: written, honest, actionable.
- **Hotfix capability (5%)**: a 1-line bug fix can be deployed in < 4 hours.

## Senior notes

The capstone is the test. Everything from modules 1-14 comes together. The patterns, the architecture, the build pipeline, the profiling, the platforms, the multiplayer (or not), the threading. This is where you prove you can ship.

Ship. That is the senior's job. Not "design well" or "code well" or "architect well." Ship. The shipped game is the test. The unshipped game is the test you didn't take.

A small shipped game is worth more than a large unshipped game. A 30-day roguelike on TestFlight is a real product. A 2-year MMO in source control is a project. The senior ships.

The spec is the contract. If it's not in the spec, it doesn't ship. The senior says no to features. "Can you add multiplayer?" "It's not in the spec." "Can you add procedural levels?" "It's not in the spec." The spec protects the schedule.

The buffer is the schedule. The 2 buffer days are not optional. They are the difference between "we shipped on time" and "we shipped 2 weeks late." Allocate them explicitly.

The retrospective is the input to the next project. The senior writes it within 7 days, while the lessons are fresh. The retrospective is the document that prevents the same mistakes in the next project.

The hotfix capability is the senior's promise. "We can fix a critical bug in 4 hours." The team that can do this is the team that retains players. The team that takes 2 weeks to fix a bug is the team that loses them.

The crash reporting is the feedback loop. Without it, you're flying blind. The senior instruments crash reporting on day 1, not on launch day. The data from day 1 is the data that catches the regressions on day 30.

The lowest-spec device is the test target. The senior tests on the slow device from week 1, not week 4. The slow device shows the real cost. The fast device hides the bugs.

The marketing is not optional. A shipped game that no one knows about is a product that no one plays. The senior allocates day 26 to marketing. The tweet, the TikTok, the devlog, the Reddit post. The marketing is part of shipping.

The post-launch triage is the discipline. Every bug report is triaged. Every P0 is fixed in 24 hours. Every P1 is fixed in the week. The senior maintains the triage process. The process is the product.

The shipped game is the deliverable. The retrospective is the input. The next project is the output. The senior's loop is: ship, learn, ship, learn, ship. The capstone is one iteration of the loop.

Ship it.
