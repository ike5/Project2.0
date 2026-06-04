# Challenge 14 — Ship & Share

Notes in [`solutions/`](./solutions/).

## Tasks
1. **Two-platform thinking.** Produce the macOS build, and describe what changes to
   target **WebGL** instead (build support module, no filesystem, async loading). You
   don't have to publish it — just enumerate the differences.

2. **Shrink a frame spike.** Use the **Profiler** to find any per-frame allocation or a
   `GetComponent`/`Find` call in `Update`. Fix it (cache in `Awake`) and confirm the
   spike is gone. Report what you changed.

3. **Object pooling (stretch).** Replace `Instantiate`/`Destroy` of coins/pickups with a
   small **object pool** (reuse a fixed set of disabled objects). Explain why pooling
   reduces GC stutter.

4. **README for your game.** Write a short `README.md` for your game project: controls,
   goal, how to build/run, and a credits/asset-license note. (Treat it like handing the
   project to a teammate — a support mindset!)

## Success criteria
- [ ] A runnable macOS `.app`, plus a correct WebGL-differences summary.
- [ ] A measured-and-fixed per-frame allocation/lookup.
- [ ] (Stretch) Pooling replaces Instantiate/Destroy with reasoning.
- [ ] A clear game README a teammate could follow.

---

## 🎓 You finished the course

You took C# from syntax to **supporting real .NET applications** (APIs, EF Core,
logging, debugging, deployment) and to **shipping Unity games** (2D, 3D, physics, UI,
audio, builds). That's the full arc you set out to learn. Keep building — and keep the
[cheatsheets](../cheatsheets/) and [glossary](../GLOSSARY.md) handy.
