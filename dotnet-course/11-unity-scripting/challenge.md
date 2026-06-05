# Challenge 11 — Scripting Fluency

Notes/solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Clamp to screen.** Extend `TransformMover` so the player can't leave a rectangular
   bound (e.g. x and y within ±8). Use `Mathf.Clamp`.

2. **Rotator component.** Write a `Rotator : MonoBehaviour` that spins its GameObject at
   a configurable degrees-per-second around Z, frame-rate independent. Attach it to the
   Coin prefab so spawned coins spin.

3. **Timed auto-spawn.** Modify `Spawner` to also spawn automatically every
   `spawnInterval` seconds (from `GameSettings`) using a coroutine or an accumulated
   timer in `Update` — without blocking.

4. **Lifecycle quiz (short answer).** For each, name the best lifecycle method and why:
   (a) caching a `GetComponent` reference, (b) applying a jump force, (c) reading
   per-frame keyboard input, (d) one-time score reset at level start.

5. **.NET vs Unity (short answer).** You need to wait 2 seconds then show a message.
   Why would you use a **coroutine** here instead of `await Task.Delay(2000)`?

## Success criteria
- [ ] Player is clamped within bounds via `Mathf.Clamp`.
- [ ] A reusable `Rotator` spins coins at a tunable speed (deltaTime-correct).
- [ ] Auto-spawn works on an interval without freezing the game.
- [ ] Correct lifecycle choices with justification.
- [ ] Sound reasoning for coroutine vs Task in Unity (main-thread / engine timing).
