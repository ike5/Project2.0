# Challenge 14: Production-Grade Architecture for a Small Game

**Time**: 4 hours
**Goal**: Build a small game (a complete vertical slice) using the senior patterns. The game has 3 enemy types, 3 tower types, a wave system, save/load, and a config-driven difficulty system. The architecture must be the kind a senior would be proud of.

## Scope

A small tower defense game. Place towers, spawn waves of enemies, prevent them from reaching the exit. Win when all waves are cleared. Lose if 10 enemies reach the exit.

The architecture:
- ScriptableObject configs for enemies, towers, waves, and difficulty.
- State machine for enemy AI (Patrol, Chase, Attack, Dead).
- Command pattern for tower placement and upgrade.
- Object pooling for projectiles and enemies.
- Event bus for game events (enemy killed, tower placed, wave started).
- Async save/load.
- VContainer for DI.
- ECS for the projectile and damage simulation (the hot path).
- MonoBehaviour for the UI, the input, the scene management.

## Requirements

### 1. ScriptableObject configs

- `EnemyConfig`: name, max health, speed, damage, gold reward, sprite.
- `TowerConfig`: name, range, fire rate, damage, projectile config, sprite.
- `ProjectileConfig`: speed, lifetime, sprite.
- `WaveConfig`: list of (enemy type, count, delay between spawns).
- `LevelConfig`: list of waves, gold to start, lives to start.
- `DifficultyConfig`: easy/normal/hard. Modifies enemy stats, gold, lives.

### 2. State machine

Each enemy has 4 states: Patrol, Chase, Attack, Dead. Transitions:
- Patrol -> Chase: enemy sees a tower in range.
- Chase -> Attack: enemy in tower's range.
- Chase -> Patrol: tower destroyed.
- Attack -> Dead: enemy health <= 0.
- Any -> Dead: enemy reaches the exit (counts as a life lost).

Each state is a class implementing IState. The state classes are pooled (so we don't allocate per state change).

### 3. Command pattern

- `PlaceTowerCommand`: places a tower at a position. Undo removes it.
- `UpgradeTowerCommand`: upgrades a tower (level 1 -> 2 -> 3). Undo downgrades.
- `SellTowerCommand`: sells a tower for gold. Undo restores it.
- `UndoRedoStack`: holds the command history.

### 4. Object pooling

- `ProjectilePool`: pre-allocated, returns Projectile.
- `EnemyPool`: pre-allocated, returns Enemy.
- `VfxPool`: pre-allocated, returns ParticleSystem.

### 5. Event bus

- `GameEventBus`: static class with C# events.
- Events: `OnEnemyKilled`, `OnEnemyReachedExit`, `OnTowerPlaced`, `OnTowerSold`, `OnWaveStarted`, `OnWaveEnded`, `OnGameOver`.
- Listeners: UI (health bar, gold counter, wave counter), audio (SFX), analytics (telemetry).

### 6. Async save/load

- `SaveSystem.SaveAsync(SaveData)`: serializes, writes atomically.
- `SaveSystem.LoadAsync()`: reads, deserializes, version-checks.
- SaveData: gold, lives, placed towers (with positions and levels), current wave.
- Auto-save: every 30 seconds during gameplay.

### 7. DI with VContainer

- `GameLifetimeScope`: registers all services.
- Services: `GameStateService`, `WaveService`, `EconomyService`, `EventBus` (if not static), `SaveSystem`.

### 8. ECS for the hot path

The damage simulation (projectile vs enemy) runs in DOTS:
- `Projectile` component: position, velocity, damage, lifetime.
- `Enemy` component (in ECS, separate from the MonoBehaviour enemy): health.
- `DamageSystem` (ISystem, Burst): every frame, check projectile-enemy collisions, apply damage, despawn dead projectiles, decrement health.

The MonoBehaviour enemies are pooled. When the pool spawns a new enemy, an ECS entity is created. When the pool returns an enemy, the ECS entity is destroyed. The MonoBehaviour reads the position from the ECS entity every frame.

### 9. UI

- HUD: gold, lives, wave number, current objective.
- Build menu: list of towers, drag to place.
- Tower upgrade panel: shows stats, upgrade/sell buttons.
- Pause menu: save, load, quit.

### 10. The complete game

- 5 levels (each with 3 waves).
- Difficulty selector (easy/normal/hard).
- Save slot selection (3 slots).
- Settings menu (audio, graphics, controls).
- Game over screen (retry, main menu).

## Out of scope

- Multiplayer.
- Procedural levels.
- Custom asset pipeline.
- Online leaderboard.

## Deliverables

1. The Unity project, buildable and runnable.
2. A `ARCHITECTURE.md` document with:
   - System diagram.
   - Pattern usage: which pattern is used where, and why.
   - The DI container graph.
   - The ECS world structure.
3. A `PATTERNS.md` document with code samples of each pattern in use.
4. A short video (5 minutes) showing the game in action.

## Acceptance criteria

| Criterion | Pass |
|-----------|------|
| Game is playable end-to-end | required |
| All 5 waves completable on normal difficulty | required |
| ScriptableObject configs drive gameplay | required |
| State machine has clean Enter/Update/Exit | required |
| Command pattern with Undo/Redo works | required |
| Object pool eliminates Instantiate per-frame | required |
| Event bus is the only communication path | required |
| Save/load works, atomic, versioned | required |
| DI container wires services | required |
| ECS handles the damage simulation | required |
| UI responds to events | required |
| 60 fps on Pixel 4a with 100 enemies on screen | required |
| Architecture documentation | required |

## Grading rubric

- **Architecture correctness (25%)**: patterns are used appropriately, not over-applied.
- **Code quality (25%)**: SOLID-ish, no globals (except where justified), testable.
- **Performance (20%)**: 60 fps on the target device, no GC alloc per frame in the hot path.
- **Completeness (15%)**: the game is end-to-end playable.
- **Documentation (15%)**: ARCHITECTURE.md and PATTERNS.md are clear and complete.

## Senior notes

The architecture is the product. The game is what the player sees; the architecture is what the team lives with. A senior's job is to make the architecture invisible to the player and obvious to the next developer.

The pattern is the wrong question. The question is: what is the simplest code that solves the problem? The pattern is the answer when the simple code becomes complex. Don't reach for the state pattern when a switch works. Don't reach for DI when a constructor parameter works.

The hybrid is the answer. ECS for the hot path, MonoBehaviour for the rest. Most of your code is MonoBehaviour. The 5% that is ECS is the part that runs 10,000 times per frame. The boundary is small, well-defined, and the right tradeoff.

Pool the hot path. Don't pool everything. The pool has overhead. For an enemy that spawns once per second, pooling is more code with no benefit. For a projectile that spawns 60 times per second, pooling is the difference between 60 fps and 22 fps.

The state machine pays off when the transitions are non-trivial. A 3-state enemy with distance-based transitions is fine in a switch. A 7-state boss with conditional transitions, animations, and effects per state is the state pattern. Pick the right tool.

The command pattern is for undo/redo and replay. If you don't have either, the command pattern is over-engineering. If you do, the command pattern is the only way.

The event bus is a maintenance hazard if overused. Every event is a hidden dependency. The publisher doesn't know who listens. The listener doesn't know who publishes. Use it for cross-system communication (UI to game logic), not for in-system communication (combat to combat).

VContainer is fast, source-generated, IL2CPP-friendly. Use it. Zenject is older, slower, reflection-heavy. Don't use it for new code.

ScriptableObjects are the data backbone. The code reads configs. The configs are in the project. Designers edit configs. Code doesn't change for balance tweaks. This is the senior way.

Save/load is the canary. If your save/load is brittle, your architecture is brittle. If your save/load is clean, your architecture is probably clean. The save/load test: can you add a new field to the save format and have old saves still load? If yes, the architecture is right.

Ship it.
