# Challenge 12 — Reference Solution

Most of this is editor work plus the two scripts here:
[`GameManagerExtended.cs`](./GameManagerExtended.cs) and [`Hazard.cs`](./Hazard.cs).
The shared [`HudController`](../../unity-scripts/2d/HudController.cs) gained a
`SetTimer(int)` method and an optional `timerText` field.

> **Wiring note:** this solution uses a new class `GameManagerExtended` (Unity requires
> the file name to match the class name, so it can't reuse `GameManager.cs`). If you
> adopt it, update `Coin.cs` to call `GameManagerExtended.Instance?.AddScore(value)`
> instead of `GameManager.Instance`, and remove/disable the original `GameManager`
> component so there's only one manager in the scene.

### 1. Lose condition (Hazard)
- Create a red square, add a **trigger** `BoxCollider2D`, add `Hazard`.
- `Hazard.OnTriggerEnter2D` → `GameManagerExtended.Instance.Lose("Game Over")`.
- `End(...)` disables the assigned `PlayerMovement2D` so the player freezes, shows the
  message, and schedules a restart.

### 2. Timer
- `GameManagerExtended.Update` subtracts `Time.deltaTime` from `_timeLeft` and calls
  `hud.SetTimer(Mathf.CeilToInt(_timeLeft))`. At `<= 0`, it calls `Lose("Time's up!")`.
- Add a third TMP text `TimerText`, wire it to the HUD's **Timer Text** field.

### 3. Restart
- `End(...)` calls `Invoke(nameof(Restart), 2f)`; `Restart()` reloads the active scene
  via `SceneManager.LoadScene(buildIndex)`. (Make sure the scene is added to **File →
  Build Settings → Scenes In Build**.)

### 4. Difficulty from a ScriptableObject
- Reference a `GameSettings` asset for `coinsToWin` (and add `timeLimit`, `moveSpeed`
  fields to `GameSettings`). Make easy/hard assets and swap which one is assigned.

### 5. Stretch
- **Speeding spawns:** in the spawner coroutine, shrink the interval over time
  (`interval = Mathf.Max(0.3f, interval * 0.95f)` each spawn).
- **High score with PlayerPrefs:**
  ```csharp
  int best = PlayerPrefs.GetInt("HighScore", 0);
  if (_score > best) { PlayerPrefs.SetInt("HighScore", _score); PlayerPrefs.Save(); }
  ```
  `PlayerPrefs` persists simple values across runs — handy for high scores/settings.
