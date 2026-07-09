# Module 09: Multiplayer with Netcode for GameObjects and Netcode for Entities

This module covers Unity's two networking stacks: **Netcode for GameObjects (NGO)** for MonoBehaviour-style games and **Netcode for Entities (NFE)** for DOTS/ECS games. By the end you will be able to pick the right stack for a project, build a server-authoritative game with client prediction, and understand the senior-level patterns that separate a working prototype from a shipped multiplayer title.

## 1. Topology: Client, Server, Host

Three roles. Pick one per process.

- **Server**: authoritative. Owns simulation. No rendering by default but can render.
- **Client**: receives state, sends inputs. Renders.
- **Host**: server + client in one process. Used for couch co-op, listen servers, and dev.

In NGO 2.x the NetworkManager is the entry point. It exposes `NetworkManager.Singleton.IsServer`, `.IsClient`, `.IsHost`. Always branch on these, never on transport state.

```csharp
if (NetworkManager.Singleton.IsServer) ServerTick();
if (NetworkManager.Singleton.IsClient) ClientTick();
```

A senior rule: server code and client code are different. Do not put them in the same `Update`. The server is allowed to mutate state directly; the client must wait for replication. Use `#if UNITY_SERVER` for server-only code, but prefer the IsServer/IsClient branch for code that runs in both contexts (the build target is the same).

## 2. NetworkManager and UnityTransport

NetworkManager is the orchestrator. UnityTransport (UTP) is the default transport. Configure the transport in the inspector: connection data (IP/port), relay (if using Unity Relay), and protocol type (UnityTransport uses UDP with reliability on top).

A typical startup:

```csharp
public async Awaitable StartHostAsync(ushort port = 7777)
{
    var transport = NetworkManager.Singleton.GetComponent<UnityTransport>();
    transport.SetConnectionData("127.0.0.1", port);

    if (!NetworkManager.Singleton.StartHost())
        throw new System.Exception("Host failed to start");

    await Awaitable.NextFrameAsync();
}
```

Wait at least one frame after start before accessing spawned objects. The spawn pipeline is deferred to the next NetworkUpdate.

Common pitfalls:
- Forgetting to add NetworkManager to the DontDestroyOnLoad scene or marking it persistent. NGO does not survive scene loads by default. Either mark it `DontDestroyOnLoad` in your bootstrap, or set `NetworkConfig.PlayerPrefab` correctly and accept the limitation.
- Running two NetworkManagers in the same process. Only one NetworkManager.Singleton can exist. Use NetworkManager pooling for editor testing only.

## 3. NetworkObject and Network Prefabs

A `NetworkObject` is a component that gives identity to a GameObject across the network. Every replicated prefab needs one. The prefab must be registered in the `NetworkManager.NetworkConfig.Prefabs` list — drag the prefab in, or register at runtime with `AddNetworkPrefab`.

The NetworkObject's GlobalObjectIdHash is how the server tells clients "spawn this prefab." If the hash mismatches between server and client builds, spawns silently fail. This is the number one cause of "it works in editor, fails in build" — both server and client builds must be from the same prefab GUID.

Spawn flow:

```csharp
// server
var instance = Instantiate(prefab, position, rotation);
instance.Spawn(destroyWithScene: true);

// client: instance appears after a round-trip
```

Despawn:
```csharp
instance.Despawn(destroy: true);
// or
NetworkObject.DespawnAll();  // bulk
```

## 4. NetworkBehaviour lifecycle

NetworkBehaviour gives you `OnNetworkSpawn` and `OnNetworkDespawn`. These are the only safe places to subscribe to NetworkVariables, RPCs, and references. The component's `NetworkObject.IsSpawned` is true between these callbacks. Anything in `Awake`/`Start` may run before the network identity is valid.

```csharp
public class PlayerHealth : NetworkBehaviour
{
    public NetworkVariable<int> Health = new(100);

    public override void OnNetworkSpawn()
    {
        Health.OnValueChanged += OnHealthChanged;
    }

    public override void OnNetworkDespawn()
    {
        Health.OnValueChanged -= OnHealthChanged;
    }
}
```

Do not rely on `Update` to read NetworkVariable values for logic. The replication tick is decoupled from Update. Read in OnValueChanged or in `NetworkUpdate(NetworkUpdateStage.Tick)`.

## 5. RPCs: ClientRpc, ServerRpc, and the new universal RPCs

NGO 2.x has two RPC styles. The old `[ServerRpc]` / `[ClientRpc]` attributes still work but are deprecated. The new style uses a single `[Rpc(SendTo.X)]` attribute.

```csharp
[Rpc(SendTo.Server)]
public void RequestFireRpc(Vector3 origin, Vector3 direction) { /* server validates */ }

[Rpc(SendTo.NotMe)]  // everyone except the caller
public void PlayFireFxRpc(Vector3 origin) { /* everyone else plays the FX */ }
```

SendTo targets:
- `Server` - to the server (was ServerRpc)
- `NotServer` - to all clients (was ClientRpc excluding owner)
- `Owner` - to the owner client
- `NotOwner` - to everyone except the owner
- `Everyone` - to all clients and the server
- `Me` - to the calling client (a way to "call back" the requester)
- `NotMe` - to everyone except the caller
- `ClientsAndHost` - all clients including host
- `SpecifiedInParams` - explicit connection list

Senior rules:
- All RPC parameters must be `INetworkSerializable` or built-in serializable types. No passing `GameObject` directly.
- RPCs are not reliable by default. Use the `Reliable` parameter for state changes; use `Unreliable` for high-frequency cosmetic events (tracers, hit sparks).
- Never put business logic in an RPC body. The RPC should set a NetworkVariable or call into a server method. The actual logic lives in one place (the server) and the RPC is a thin transport.

## 6. NetworkVariable

`NetworkVariable<T>` is server-write, everyone-read by default. The server writes, the clients see the change via OnValueChanged. This is your primary state replication tool.

```csharp
public NetworkVariable<int> Ammo = new(
    value: 30,
    readPerm: NetworkVariableReadPermission.Everyone,
    writePerm: NetworkVariableWritePermission.Server);
```

For custom types, implement `INetworkSerializable` and `IEquatable<T>` (or pass an equality comparer to the constructor):

```csharp
public struct PlayerState : INetworkSerializable, IEquatable<PlayerState>
{
    public Vector3 Position;
    public Quaternion Rotation;
    public int Health;

    public void NetworkSerialize<T>(BufferSerializer<T> s) where T : IReaderWriter
    {
        s.SerializeValue(ref Position);
        s.SerializeValue(ref Rotation);
        s.SerializeValue(ref Health);
    }

    public bool Equals(PlayerState other) =>
        Position == other.Position &&
        Rotation == other.Rotation &&
        Health == other.Health;
}

public NetworkVariable<PlayerState> State = new(default,
    NetworkVariableReadPermission.Everyone,
    NetworkVariableWritePermission.Server);
```

The default replication tick is 30 Hz. Bump it via `NetworkManager.NetworkConfig.TickRate`. Higher tick rate costs bandwidth. For 60 Hz you need a fast transport (UTP) and a server with bandwidth headroom.

Delta tracking: NGO 2.x supports per-field dirty tracking through IEquatable. Implementing IEquatable on your struct is the difference between full-state replication and delta replication. Always do it.

## 7. NetworkBehaviour, NetworkTransform, and the camera

NetworkTransform is the built-in replicated transform. Use it for cosmetic-only objects — debris, doors, anything the client cannot affect. Do not use it for player movement; the latency is too high for an action game.

For a player, the senior pattern is:
1. Client reads input locally and predicts movement (client-side simulation).
2. Client sends input commands to the server.
3. Server simulates the same input authoritatively.
4. Server sends back authoritative state.
5. Client reconciles if its predicted state diverges from authoritative state.

This is client-side prediction with server reconciliation. The next section covers the implementation in NGO.

## 8. Client-side prediction in NGO

```csharp
public class PredictedPlayer : NetworkBehaviour
{
    [SerializeField] float moveSpeed = 5f;

    struct InputCommand : INetworkSerializable
    {
        public uint Tick;
        public Vector2 Move;
        public float Yaw;

        public void NetworkSerialize<T>(BufferSerializer<T> s) where T : IReaderWriter
        {
            s.SerializeValue(ref Tick);
            s.SerializeValue(ref Move);
            s.SerializeValue(ref Yaw);
        }
    }

    // server: ring buffer of last N states
    readonly InputCommand[] _history = new InputCommand[128];
    int _historyHead;

    // client: predicted state
    Vector3 _predictedPosition;
    InputCommand _lastPredicted;

    [Rpc(SendTo.Server, Delivery = RpcDelivery.Reliable)]
    public void SubmitInputRpc(InputCommand cmd, RpcParams rpcParams = default)
    {
        if (rpcParams.Receive.SenderClientId != OwnerClientId) return;
        ApplyInput(cmd);
        _history[_historyHead++ & 127] = cmd;
    }

    void Update()
    {
        if (!IsOwner) return;
        var cmd = new InputCommand
        {
            Tick = NetworkManager.LocalTime.Tick,
            Move = Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"),
            Yaw = Camera.main.transform.eulerAngles.y
        };
        ApplyInput(cmd);
        _lastPredicted = cmd;
        SubmitInputRpc(cmd);
    }

    void ApplyInput(InputCommand cmd)
    {
        var fwd = Quaternion.Euler(0, cmd.Yaw, 0) * Vector3.forward;
        transform.position += (fwd * cmd.Move.y + Vector3.right * cmd.Move.x) * moveSpeed * Time.deltaTime;
    }
}
```

This is the simplest form. A production implementation reconciles on every state update by re-running inputs from the history until the position matches. See the lab for the reconciliation pass.

## 9. Netcode for Entities (NFE) overview

NGO is for MonoBehaviour games. NFE is for DOTS/ECS games. The mental model is different:

- **Ghost**: the ECS equivalent of a NetworkObject. A ghost is a replicated entity.
- **GhostAuthoringComponent**: marks a GameObject to be baked into a ghost.
- **GhostFieldAttribute**: marks a component field as replicated. Only marked fields are sent.
- **Snapshot**: a delta-encoded buffer of all dirty ghost fields sent from server to clients.
- **Prediction**: built-in. The client runs a "predicted simulation world" alongside the "presentation world" and reconciles automatically.
- **Interpolated vs predicted ghosts**: some ghosts (other players) interpolate; the local player predicts.

You annotate your IComponentData with `[GhostComponent]` and individual fields with `[GhostField]`. The codegen produces a serialization spec that runs at runtime.

```csharp
public struct PlayerInput : IInputComponentData
{
    public float2 Move;
    public float Yaw;
}

public struct PlayerState : IComponentData
{
    [GhostField] public float3 Position;
    [GhostField] public quaternion Rotation;
    [GhostField] public int Health;
}
```

The PredictedSimulationSystemGroup runs ahead of the presentation. NFE handles the reconciliation buffer, rollback, and re-simulation for you. This is the "ECS for the hot path" pattern from module 14.

## 10. Snapshot system and bandwidth

The snapshot system in NFE streams ghost deltas to clients at a fixed rate (default 60 Hz, configurable). Each snapshot is the diff between the previous and current state of every ghost the client cares about. Interest management filters which ghosts are in the snapshot for which client.

Senior bandwidth rules:
- Replicate only what changes. Static objects should not be in the snapshot.
- Quantize. Use `GhostField(Quantization = 1000, Smoothing = SmoothingAction.InterpolateAndExtrapolate)` for positions to send as 16-bit instead of 32-bit floats.
- Tick rate is the cost. 60 Hz snapshot on 64 players with 10 replicated fields = bandwidth disaster. Profile in module 12.

## 11. Prediction vs interpolation

Two distinct visual strategies:
- **Predicted**: client runs the same simulation as the server, ahead of time. Used for the local player.
- **Interpolated**: client renders at a delay (one RTT + a few frames), smoothing between received states. Used for remote players, projectiles, anything the local player does not own.

In NFE, set `GhostOwner` to mark predicted ghosts and use the default interpolation for others. In NGO you do this by hand or with `NetworkTransform`'s interpolation mode.

## 12. Lag compensation

Server-side lag compensation rewinds the world state to validate a player's hit. The classic case: player A shoots at where player B is rendered (interpolated position), but by the time the shot arrives at the server, player B has moved. The server rewinds B's position to the time of A's shot, performs a hit test, and accepts the kill.

In NGO you implement this with a per-player history buffer. In NFE, the `GhostPredictionSmoothingSystem` and lag compensation are opt-in via `LagCompensationConfig` on the client.

```csharp
// NGO lag compensation skeleton
[Rpc(SendTo.Server, Delivery = RpcDelivery.Unreliable)]
public void FireRpc(Vector3 origin, Vector3 direction, double clientTime)
{
    var historyTick = _timeSystem.TickAtTime(clientTime);
    var rewindPos = _history.GetPosition(shooter.OwnerClientId, historyTick);
    var hit = _hitTest.RaycastAtTick(rewindPos, direction, historyTick);
    if (hit.HasValue) ApplyDamage(hit.Value.Entity, 25);
}
```

## 13. Authority and trust

The server is always the source of truth. The client is untrusted. Every server-authoritative check happens in the server method that the RPC calls into. Never trust a client RPC's payload for damage, scoring, or state changes.

```csharp
[Rpc(SendTo.Server)]
public void BuyItemRpc(int itemId, RpcParams p = default)
{
    if (p.Receive.SenderClientId != OwnerClientId) return;       // identity
    if (!_shop.HasItem(itemId)) return;                          // inventory
    if (_economy.GetCoins(OwnerClientId) < _shop.Price(itemId)) return; // funds
    _economy.Spend(OwnerClientId, _shop.Price(itemId));
    _shop.Grant(OwnerClientId, itemId);
}
```

This is the authority pattern. Every server-side method that mutates state has three checks: identity, preconditions, effect. If you skip any of them, you ship a cheatable game.

## 14. Deterministic lockstep

For RTS, fighting games, and physics-heavy games, deterministic lockstep is sometimes the right model. Both clients run the exact same simulation given the exact same inputs, no snapshots, no replication. All players send inputs to all other players; the simulation runs at the same tick on every machine.

This requires:
- Deterministic floating point (Unity's default is not — see module 6 on Burst and deterministic math).
- No `Time.deltaTime` (use fixed ticks).
- Identical starting state (hashed).
- No async file IO during the simulation.

Lockstep in Unity 6 is achievable with Burst and the DOTS FixedStepSimulationSystemGroup. NGO does not give you this for free. Most production RTS use a custom netcode layer.

## 15. Interest management

By default NGO replicates every NetworkObject to every client. For a 64-player battle royale, this is 64x bandwidth. Interest management filters which objects go to which clients.

NGO has `NetworkObject` interest management via `NetworkObject.CheckObjectVisibility`. Return false and the object is not replicated to that client.

```csharp
public override bool CheckObjectVisibility(NetworkObject clientTarget)
{
    var dist = Vector3.Distance(transform.position, clientTarget.transform.position);
    return dist < _viewRadius;
}
```

NFE has the `GhostImportance` system and the `GhostDistanceImportance` scaling. You can also use `GhostFilter` for archetype-based filtering.

## 16. Senior workflow

1. Start with NGO. It is faster to prototype in and 80% of multiplayer games do not need ECS.
2. Move to NFE only when the simulation is the bottleneck (hundreds of replicated entities per tick).
3. Authoritative server, predicted client, interpolated remote.
4. Profile bandwidth at 32, 64, 128 players in a stress test before shipping.
5. Test with simulated latency: NGO has `NetworkSimulator` in the multiplayer tools package.
6. Lag compensate hit detection server-side.
7. Never trust a client.
8. Plan for relay/transport from day one. Self-hosted servers do not scale.

## What to read next

- Module 10: async lifetimes for `Awaitable`-based host startup.
- Module 11: IL2CPP stripping for netcode — code stripping removes reflection paths.
- Module 12: profiling replication cost.
- Module 13: headless Linux build for dedicated server.
- Module 14: command pattern for input, save/load for replay.
