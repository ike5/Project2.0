# Challenge 12: Profile a Production-Grade Game

**Time**: 4 hours
**Goal**: Take a real game scene with multiple systems, profile it on the target device, identify the top 5 bottlenecks, fix them, and document the result. The deliverable is a profile report that a senior would be proud of.

## Scope

A small RPG scene: 1 player, 50 NPCs, 200 interactable objects, a UI, and a quest system. The scene runs at 45 fps on a Pixel 4a. Target: 60 fps. The bottlenecks are unknown — your job is to find them.

The game has:
- An `NPC` system: each NPC has a state machine (idle, walk, talk).
- A `Quest` system: 20 active quests, each with 5 objectives.
- A `UI` system: HUD, dialogue box, inventory panel.
- A `Physics` system: 200 rigidbodies for interactable objects.
- A `Save` system: writes save data every 30 seconds.
- A `Network` system: 8 players in a multiplayer session (NGO).

## Requirements

### Phase 1: Profile (60 min)

1. Set up the scene. Use the `com.unity.memoryprofiler` and `com.unity.profileanalyzer` packages.
2. Build a development build for Android (ARM64). Deploy to a Pixel 4a (or equivalent).
3. Run the scene for 60 seconds. Capture:
   - Live Profiler trace (5 minutes).
   - Memory Profiler snapshot (start), 30s snapshot, 60s snapshot.
4. Save the Profile Analyzer data for analysis.
5. Document the baseline:
   - Median frame time.
   - p95 frame time.
   - p99 frame time.
   - GC alloc per frame.
   - GC events per minute.
   - Peak memory.
   - Draw calls.
   - Setpass calls.

### Phase 2: Identify (45 min)

1. Open the Profiler trace. Find the top 5 most expensive systems by total time.
2. For each, find the specific function call that is the bottleneck.
3. Write a one-paragraph description of each bottleneck:
   - What is it doing?
   - Why is it slow?
   - What is the fix?

### Phase 3: Fix (90 min)

1. For each bottleneck, implement a fix.
2. The fixes should be production-quality, not quick hacks:
   - Use a pool instead of Instantiate.
   - Use a spatial hash instead of O(n^2).
   - Use Burst for the physics integration.
   - Cache the UI rebuilds.
   - Move the save to async.
3. Re-profile after each fix. Record the new numbers.
4. Document each fix in a `FIXES.md` file with before/after numbers.

### Phase 4: Verify (45 min)

1. Run the scene for 10 minutes. Confirm the frame time is stable (no memory growth causing slowdown).
2. Run the scene for 5 minutes with the network stress test (8 players in combat). Confirm 60 fps is maintained.
3. Capture a final Memory Profiler snapshot. Confirm no leak.
4. Write a `REPORT.md` with:
   - Executive summary: "we went from 45 fps to 60 fps by fixing X, Y, Z."
   - Baseline numbers.
   - Final numbers.
   - List of fixes with descriptions and numbers.
   - What was intentionally not fixed and why (if anything).

## Deliverables

1. The Unity project with the optimized scene.
2. A `REPORT.md` with the profile data.
3. A `FIXES.md` describing each fix.
4. The Profiler capture files (or paths to them).
5. The Memory Profiler snapshot files.
6. The Profile Analyzer export.

## Acceptance criteria

| Criterion | Pass |
|-----------|------|
| Profile data captured on real device | required |
| Top 5 bottlenecks identified | required |
| Each fix is production-quality | required |
| Frame time improved to 60 fps on Pixel 4a | required |
| No memory leak over 10 minutes | required |
| REPORT.md is clear and data-driven | required |
| Profile captures and snapshots archived | required |
| Each fix has before/after numbers | required |

## Grading rubric

- **Profile methodology (20%)**: correct tools, correct device, correct metrics.
- **Bottleneck identification (20%)**: the right 5 bottlenecks, well-understood.
- **Fix quality (30%)**: production code, not hacks. No premature optimization.
- **Verification (20%)**: before/after numbers, sustained test, no regression.
- **Documentation (10%)**: REPORT.md and FIXES.md are clear and honest.

## Senior notes

Don't profile on the dev machine. The dev machine is 10x faster than the Pixel 4a. The bottlenecks you find on the dev machine are different from the ones on the device. Profile on the device.

Don't optimize what you can guess. Profile first, optimize what the Profiler tells you. The most expensive line of code is rarely the one you suspected.

Don't fix all 50 bottlenecks. Fix the top 5. The top 5 is usually 80% of the frame time. The other 45 are 1% each. Fix the big ones, leave the small ones.

Don't write a fix that makes the code 10x more complex for a 0.5 ms improvement. The cost of complexity is bugs. The benefit of 0.5 ms is invisible. Pick your battles.

Don't trust single-frame profiling. The variance is high. A spike at frame 2300 doesn't tell you the median is high. Use the Profile Analyzer for distribution.

Don't ship a "feels faster" claim. Ship numbers. Frame time, GC alloc, memory. Numbers don't lie.

Don't ignore the render thread. If main thread is 5 ms and render thread is 20 ms, the frame is 20 ms. The main thread is not the bottleneck. Profile the render thread.

Don't forget the GC. A 2 KB allocation per frame is 120 KB/min. The GC will trigger. The pause will hitch. The game will stutter. Zero GC alloc is the goal. If you can't, minimize.

Don't ship without a soak test. A 10-minute test catches memory leaks that a 1-minute test misses. Run the game for an hour, watch the memory. If it grows, you have a leak.

Don't forget to document the why. The fix without a reason is a hack. The fix with a reason is engineering. Future you, reading the code in 6 months, will thank you.

Ship it.
