# Challenge 12 — Make It a Real Game

Notes/solution in [`solutions/`](./solutions/). Try first — most of this is in the
editor + small script edits.

## Tasks
1. **Lose condition.** Add a `Hazard` (a red square, trigger) that ends the game on
   contact with the player: show "Game Over" and stop player movement. Add a
   `GameManager.Lose()` method.

2. **Timer.** Add a countdown (e.g. 30s) shown in the HUD. If it hits zero before the
   player wins, trigger the lose condition. Drive it from `Update` with `Time.deltaTime`
   (or a coroutine).

3. **Restart.** On win/lose, after 2 seconds, reload the scene (`GameManager.Restart`
   via `Invoke` or a coroutine) so the game is replayable.

4. **Difficulty from a ScriptableObject.** Move `coinsToWin`, the timer length, and the
   player speed into a `GameSettings` asset and read them, so you can make easy/hard
   variants by swapping assets.

5. **Stretch:** Spawn coins on an interval that speeds up over time, and keep a
   high-score across restarts using `PlayerPrefs`.

## Success criteria
- [ ] Touching a hazard ends the game with a "Game Over" message.
- [ ] A visible countdown that can trigger a loss.
- [ ] The game auto-restarts and is replayable.
- [ ] Difficulty values come from a swappable ScriptableObject.
