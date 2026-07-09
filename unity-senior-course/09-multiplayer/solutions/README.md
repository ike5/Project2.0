# Solutions 09: Reference Implementation Notes

The lab and challenge reference solutions are too large to embed inline. The key patterns are below — full code lives in `Assets/Scripts/` in the reference repo (separate).

## 1. Reconciliation algorithm

The reconciliation pass runs on the owner client when an authoritative state arrives.

```
function Reconcile(authoritativeState, authoritativeTick):
    if authoritativeTick <= lastReconciledTick: return  // late packet, ignore
    lastReconciledTick = authoritativeTick

    // snap to authoritative
    position = authoritativeState.position
    velocity = authoritativeState.velocity

    // replay inputs from authoritativeTick+1 to current
    for cmd in inputHistory from (authoritativeTick+1) to head:
        ApplyInput(cmd)
        // predicted state diverges from authoritative again
```

Implementation requirements:
- `inputHistory` is a ring buffer. Fixed size (e.g. 256). The head pointer is the most recent input.
- `lastReconciledTick` is the tick the client has applied authoritative state for. Late packets are dropped (server is the source of truth; we do not roll back from an older snapshot).
- After replay, the predicted state and the next-input predicted state should match what the server will send. If they don't, you have a non-deterministic input pipeline. Most common cause: reading `Time.deltaTime` (variable per frame) in ApplyInput. Use a fixed step.

## 2. Server-side history for lag compensation

```csharp
public sealed class PlayerHistory
{
    public struct Snapshot
    {
        public uint Tick;
        public Vector3 Position;
    }

    readonly Snapshot[] _buffer = new Snapshot[128];
    int _head;

    public void Record(uint tick, Vector3 position)
    {
        _buffer[_head & 127] = new Snapshot { Tick = tick, Position = position };
        _head++;
    }

    public bool TryGetAtTick(uint tick, out Vector3 position)
    {
        // walk back from head; tick is monotonically increasing
        for (int i = _head - 1; i >= _head - 128 && i >= 0; i--)
        {
            if (_buffer[i & 127].Tick == tick)
            {
                position = _buffer[i & 127].Position;
                return true;
            }
        }
        position = default;
        return false;
    }
}
```

Wire `Record` into a server-only system that ticks at the server tick rate:

```csharp
public class ServerSnapshotRecorder : NetworkBehaviour
{
    [SerializeField] PlayerHistory history; // server-side, not networked
    [SerializeField] NetworkObject target;  // the player to record

    void FixedUpdate()
    {
        if (!IsServer) return;
        history.Record(NetworkManager.ServerTime.Tick, target.transform.position);
    }
}
```

## 3. Server-validated fire RPC

The reference uses the authority pattern: identity, preconditions, effect.

```csharp
[Rpc(SendTo.Server, Delivery = RpcDelivery.Unreliable)]
public void FireRpc(Vector3 origin, Vector3 direction, double clientTime, RpcParams p = default)
{
    // identity
    if (p.Receive.SenderClientId != OwnerClientId) return;

    // preconditions
    if (_cooldown.Get(p.Receive.SenderClientId) > 0) return;
    if (NetworkManager.ServerTime.Time - _lastFireTime[OwnerClientId] < 0.1) return;

    // effect
    var tick = NetworkManager.ServerTime.TickAtTime(clientTime);
    if (!_history.TryGetAtTick(tick, out var rewindOrigin)) rewindOrigin = transform.position;

    if (Physics.Raycast(rewindOrigin, direction, out var hit, _range))
    {
        var target = hit.collider.GetComponent<NetworkObject>();
        if (target != null && target.OwnerClientId != OwnerClientId)
        {
            _health.Damage(target.OwnerClientId, _damage);
            _cooldown.Set(OwnerClientId, 0.25f);
            _lastFireTime[OwnerClientId] = NetworkManager.ServerTime.Time;
        }
    }
}
```

## 4. NGO startup with Awaitable

```csharp
public async Awaitable StartHostAsync()
{
    if (NetworkManager.Singleton.IsListening) return;
    var transport = NetworkManager.Singleton.GetComponent<UnityTransport>();
    transport.SetConnectionData(_ip, _port);

    if (!NetworkManager.Singleton.StartHost())
        throw new InvalidOperationException("host start failed");

    // NGO needs at least one frame to finish spawn bookkeeping
    await Awaitable.NextFrameAsync();
    _log.Info("host ready");
}
```

Awaitable is the Unity 6 way. See module 10.

## 5. Headless dedicated server

```bash
# Linux dedicated server build target
./Builds/Server/ArenaServer.x86_64 -batchmode -nographics -port 7777 -logFile server.log
```

The server build:
- Define `UNITY_SERVER` in the build target.
- Strip rendering components (any UI Camera, AudioListener, etc., should check `#if !UNITY_SERVER`).
- `Application.targetFrameRate = 60` is fine; the simulation runs at fixed step.
- Use `[ServerRpc]` ... wait, no. The new style: `[Rpc(SendTo.Server)]`. The server-side code is normal MonoBehaviour or SystemBase code.

`UNITY_SERVER` define is auto-set by the dedicated server build target. Use it to gate all rendering init:

```csharp
void Start()
{
#if UNITY_SERVER
    Application.targetFrameRate = 60;
    QualitySettings.vSyncCount = 0;
    // disable rendering
    foreach (var cam in FindObjectsByType<Camera>(FindObjectsSortMode.None))
        cam.enabled = false;
#endif
}
```

## 6. NetworkObject spawning

For dynamic objects (coins, projectiles), use the NetworkObject.Spawn() flow:

```csharp
public NetworkObject coinPrefab;

public void SpawnCoinServer(Vector3 position)
{
    if (!IsServer) return;
    var instance = Instantiate(coinPrefab, position, Quaternion.identity);
    instance.Spawn(true); // destroyWithScene
}
```

`Spawn()` registers the instance with the network system. The client gets a spawn message, looks up the prefab by `GlobalObjectIdHash`, instantiates locally, and links it to the server's instance. Despawn is symmetric.

## 7. Persistent client ID for reconnection

```csharp
public override void OnNetworkSpawn()
{
    if (IsServer)
    {
        _clientData[OwnerClientId] = new PlayerData
        {
            Wallet = 0,
            Kills = 0,
            PersistentId = (ulong)Random.Range(0, int.MaxValue)
        };
    }
}
```

Persist the `PersistentId` and the auth token out to a JSON file server-side. On reconnect, the client sends the token in the connection data and the server restores the wallet and score to the same `OwnerClientId`. NetworkManager does not give you this for free; you implement it on top of `ConnectionApprovalCallback`.

## 8. Common bugs in the reference

- **Float drift in prediction**: storing `Time.deltaTime` in the input command causes divergence. Use a fixed step and store nothing time-related in the input, only the axis values.
- **Order of OnNetworkSpawn callbacks**: child NetworkObjects' OnNetworkSpawn fires before parent's. Do not access child state in parent's spawn.
- **RPC delivery mismatch**: a fire RPC sent as Unreliable with a despawn message in the same frame gets dropped. Use Reliable for state changes.
- **Transform write while server is interpolating**: if you set `transform.position` on the server and NetworkTransform is also replicating it, you get fights. Set the position before NetworkTransform samples, or set it via a NetworkVariable<Vector3> instead.
- **NetworkVariable default values differ between server and client builds**: the client uses the prefab default, the server uses the constructor default. Always set the same default in the prefab and the constructor.
- **Spawning before the host is fully connected**: `StartHost` returns true even before clients are listening. Wait for `OnClientConnectedCallback` on the host before spawning round-state objects.

## 9. Profiler hooks

Add a `ProfilerMarker` around the reconciliation pass and around the snapshot system:

```csharp
static readonly ProfilerMarker s_reconcileMarker = new("Player.Reconcile");
static readonly ProfilerMarker s_serializeMarker = new("Player.SerializeState");

void Reconcile(...)
{
    using (s_reconcileMarker.Auto())
    {
        // ...
    }
}
```

These show up in the profiler module view (module 12) and let you see the cost of replication vs. simulation.

## 10. What's not in the reference

- Anti-cheat. Server authority is the floor; a real game needs signed RPC payloads, rate limiting, and report systems.
- Matchmaking. Out of scope. Use Unity Matchmaker or your own.
- Relay. Use Unity Relay or a self-hosted gateway. The transport works either way; the relay is the routing layer.
- Physics determinism. The reference uses kinematic players. For dynamic physics, look at module 6 on Burst and the Unity Physics DOTS package.
