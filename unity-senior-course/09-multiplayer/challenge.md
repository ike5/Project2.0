# Challenge 09: Production-Grade Multiplayer Arena

**Time**: 3 hours
**Goal**: Deliver a small but complete 4-player multiplayer game with prediction, reconciliation, lag-compensated weapons, and a server-authoritative economy. No hand-holding. This is the module exam.

## Scope

A 4-player top-down arena. Players move, shoot, pick up coins, and respawn. Server-authoritative. Client-predicted. Lag-compensated hitscan. Server-side scoring. Single-round match with a winner.

## Requirements

### Networking

1. Use Netcode for GameObjects 2.x. Build a host + clients architecture. Support up to 4 simultaneous players.
2. Player movement is client-predicted. Server simulates authoritatively. Client reconciles against server state every tick. Reconciliation re-runs the player's input history from the last authoritative state forward. Show the predicted state and the corrected state visibly if they diverge (debug overlay).
3. All other players render interpolated. Interpolation buffer = 100 ms, with extrapolation cap of 50 ms.
4. NetworkVariable for health, score, and round state. All server-write, everyone-read. Implement IEquatable on the value type if you make a custom struct.
5. All gameplay RPCs are server-validated. Identity check, preconditions check, effect. The server must reject any RPC from a non-owner.

### Lag compensation

1. Server stores a ring buffer of 128 player position snapshots (one per server tick).
2. Hitscan weapon does a server-side raycast at the shooter's position rewound to the shooter's `clientTime`.
3. Damage only applies if the target was actually hit at the rewound time. No client-side hit detection.

### Economy and scoring

1. Coins spawn at random positions. Server picks a position; NetworkObject spawns; clients see it appear via NetworkObject spawn.
2. Walking over a coin despawns it server-side and credits the player's wallet.
3. Killing another player (bringing their health to zero) grants +1 score and 10 coins.
4. Respawning costs 5 coins (deducted from the wallet) and resets health.
5. First to 5 kills wins. Server announces a winner via a NetworkVariable change and disables input on all clients.

### Build and run

1. Provide a host build, a client build, and a headless dedicated server build. The dedicated server runs as a Linux build (see module 13).
2. Bandwidth test: simulate 4 players, run for 60 seconds, log total bytes sent and received on the host. Document the result.

### Polish

1. NetworkSimulator defaults: 80 ms RTT, 1% packet loss. The game must feel responsive.
2. Disconnect handling: if a player disconnects mid-match, server refunds their held state, removes their NetworkObject, and continues the match.
3. Reconnection: a player with the same persistent client ID can reconnect and resume their wallet and score.

## Out of scope

- Voice chat.
- Matchmaking.
- Custom relay.
- Anti-cheat beyond server authority.
- Spectator mode.

## Deliverables

1. A Unity 6 project that builds and runs in all three modes (host, client, dedicated server).
2. A `MULTIPLAYER.md` document with:
   - Architecture diagram of the replication model.
   - Tick rate and snapshot policy.
   - Bandwidth test results.
   - Reconciliation algorithm description with pseudo-code.
   - Failure modes considered (packet loss, disconnect, host migration absent).
3. A short screen recording of:
   - 4 clients connected, all moving, with NetworkSimulator latency on.
   - A kill with lag compensation on (you can use a "ghost" mode that disables the shooter's prediction to make the divergence visible).
4. Code: all source under `Assets/Scripts/`. No code in `Assets/Plugins/`. No third-party netcode beyond NGO and UTP.

## Acceptance criteria

| Criterion | Pass |
|-----------|------|
| 4 clients connect, see each other, see themselves | required |
| Local movement feels instant (predicted) | required |
| Other players move smoothly (interpolated) | required |
| Hitscan lands where the target was rendered | required |
| Server rejects forged RPCs | required |
| Round ends with a winner | required |
| Dedicated server runs headless | required |
| Disconnect handled without crash | required |
| Reconnection resumes state | bonus |
| Bandwidth log produced | required |

## Grading rubric

- **Replication correctness (40%)**: prediction + reconciliation + interpolation done right. Server authority enforced everywhere.
- **Lag compensation (20%)**: history buffer, rewind, raycast at rewinded position. Tests at 0 ms, 80 ms, 200 ms RTT.
- **Robustness (20%)**: disconnect, reconnection, host failure, packet loss.
- **Code quality (20%)**: SOLID-ish, no globals, NetworkBehaviour lifecycles correct, RPC payloads minimal.

## Senior notes

You will fail the first time you do reconciliation. The history index is off by one, or the ring buffer wraps and you read stale data, or the server tick and client tick drift. Add a `ProfilerMarker` around the reconciliation pass and watch it in the profiler (module 12). The reconciliation pass is the single most likely place to ship a bug.

Test with 200 ms RTT, not 0 ms. 0 ms is the case where bugs hide. The bug appears at 150 ms and breaks at 200 ms. If you have not tested at 200 ms, you have not tested.

Do not use `NetworkTransform` for player movement. Use it for cosmetic objects. The interpolation model is wrong for action games.

Do not use `[ClientRpc]` for fire effects. Use `[Rpc(SendTo.NotOwner)]` so the owner does not double-play. The owner plays the local FX immediately; the rest of the world gets the RPC.

Do not subscribe to NetworkVariable.OnValueChanged in Start. Always in OnNetworkSpawn, always unsubscribe in OnNetworkDespawn. Otherwise your callback fires after despawn and you have a dangling reference.

Do not assume the host is fair. The host is a player. If your game is competitive, run dedicated servers and let the clients connect to a remote IP. Local host is for development, not production.

Do not write `[ServerRpc]` new code. Use the unified `[Rpc(SendTo.Server)]`. The old attributes are deprecated; the new style lets you specify delivery and target without two separate attributes.

If you have more than 32 replicated entities per client per tick, you should be using Netcode for Entities. NGO scales to 64-128 players with light per-entity state. Beyond that, you need ECS.

Ship it.
