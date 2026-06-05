# Challenge 11 — Reference Solution

### 1. Clamp to screen
```csharp
private void Update()
{
    float h = Input.GetAxisRaw("Horizontal");
    float v = Input.GetAxisRaw("Vertical");
    var dir = new Vector3(h, v, 0f).normalized;
    var pos = transform.position + dir * (speed * Time.deltaTime);
    pos.x = Mathf.Clamp(pos.x, -8f, 8f);
    pos.y = Mathf.Clamp(pos.y, -8f, 8f);
    transform.position = pos;
}
```

### 2. Rotator
See [`Rotator.cs`](./Rotator.cs). Attach to the Coin prefab; all spawned coins spin.

### 3. Timed auto-spawn (coroutine)
```csharp
[SerializeField] private GameSettings settings;

private void Start() => StartCoroutine(AutoSpawn());

private IEnumerator AutoSpawn()
{
    while (true)
    {
        SpawnOne();
        float interval = settings != null ? settings.spawnInterval : 1.5f;
        yield return new WaitForSeconds(interval);
    }
}
```
> The coroutine yields between spawns, so the game keeps running — no blocking.

### 4. Lifecycle quiz
- **(a)** cache `GetComponent` in **`Awake`** — references set up before anything uses them.
- **(b)** apply a jump force in **`FixedUpdate`** — physics runs on the fixed clock.
- **(c)** read per-frame input in **`Update`** — once per rendered frame.
- **(d)** one-time score reset in **`Start`** (or `Awake`) — runs once at startup.

### 5. Coroutine vs Task
> Unity's APIs are **main-thread only** and timing is tied to the **engine's frame
> loop**. A coroutine resumes on the main thread in sync with frames (and respects
> pause/time-scale), so it can safely touch GameObjects/UI. `await Task.Delay` resumes
> on a thread-pool thread where touching Unity objects throws — and it ignores Unity's
> timescale/pause. Use coroutines (or `Awaitable`/UniTask) for in-game timing.
