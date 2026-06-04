# Lab 14 — Build and Ship It

**You'll:** produce a runnable macOS build and finish your game. ⏱️ ~60 min + polish.

---

## Part A — Prepare scenes
1. **File → Build Settings** (or **Build Profiles**).
2. Click **Add Open Scenes** for each scene, or drag them in. Order them: `Menu` (0) →
   `Main` (1) → `Win` (2). Index 0 is what launches first.
3. Verify scene transitions use names that are in this list (`SceneManager.LoadScene("Main")`).

## Part B — Player settings
1. In Build Settings → **Player Settings**:
   - Set **Product Name** (your game's title) and **Company Name**.
   - Optionally set a **Default Icon** (drag an image).
   - Resolution: pick **Windowed** with a sensible default size for testing.

## Part C — Build for macOS
1. Platform: **macOS** (switch platform if needed — may re-import assets once).
2. Click **Build** → choose/create an output folder (e.g. `Builds/`). Wait for it to
   finish.
3. Find the produced **`YourGame.app`** in that folder. Double-click to run it —
   **outside** the editor.

✅ You have a standalone application. (First launch on macOS may require right-click →
**Open** to bypass Gatekeeper for an unsigned app.)

> `Builds/` is git-ignored by the course `.gitignore` — you ship the `.app`, you don't
> commit it.

## Part D — Finish the game
Pick **one** game (2D or 3D) and make it feel complete:
- Menu with **Start**; **Win** (and ideally **Lose**) outcomes.
- A working **score/HUD** and at least one **sound**.
- 2–3 polish items from the Module 12/13 challenges (timer, restart, walls, pause,
  high score, spinning pickups…).

## Part E — Organize & verify
1. Tidy `Assets/` into `Scenes/`, `Scripts/`, `Prefabs/`, `Materials/`, `Audio/`,
   `Settings/`.
2. Confirm a clean `.gitignore` (no `Library/` committed). If you version this game,
   commit `Assets/`, `Packages/`, `ProjectSettings/` only.
3. Rebuild and play the `.app` start-to-finish: menu → play → win → (play again).

## Part F — Capstone B self-assessment
Score yourself with [`solutions/RUBRIC.md`](./solutions/RUBRIC.md). When the build runs
end-to-end and you can explain every script, **you've shipped a game.** 🎉

## What you learned
- Configure Build Settings/Player Settings and export a macOS `.app`.
- Mono vs IL2CPP, Development vs release builds.
- Project organization and Unity source-control hygiene.
- You shipped a finished, runnable game.

➡️ **[challenge.md](./challenge.md)** — final stretch goals and where to go next.
