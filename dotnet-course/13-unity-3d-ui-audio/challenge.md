# Challenge 13 — Round Out the 3D Game

Notes in [`solutions/`](./solutions/). Mostly editor work + small scripts.

## Tasks
1. **Main menu scene.** Add a `Menu` scene with a title and **Start** / **Quit**
   buttons. Start loads `Main`; Quit calls `Application.Quit()` (note it only truly
   quits in a build, not in the editor). Make `Menu` the first scene in Build Settings.

2. **Persistent score across scenes.** Carry the final score from `Main` into the `Win`
   scene and display it. Use a `DontDestroyOnLoad` manager or `PlayerPrefs`.

3. **Pause menu.** Toggle a pause panel with `Esc`; while paused set `Time.timeScale = 0`
   (and back to 1 on resume). Explain what `Time.timeScale = 0` does to `Update` vs
   `FixedUpdate`.

4. **Walls + fall detection.** Add walls so the ball can't roll off, and a check that
   reloads the level if the ball's `y` drops below a threshold (fell off).

5. **Audio mixer (stretch).** Route music and SFX through an **AudioMixer** with a
   master volume, and expose a volume slider in the menu.

## Success criteria
- [ ] A menu scene with working Start/Quit, set as the first build scene.
- [ ] Final score persists into the win screen.
- [ ] Esc pause freezes gameplay via `timeScale` and resumes cleanly.
- [ ] Falling off reloads the level; walls contain the ball.
