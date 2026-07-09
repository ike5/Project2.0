# Lab 09: Build a Server-Authoritative Multiplayer Prototype

**Time**: 75 minutes
**Goal**: A host-authoritative 4-player arena with predicted local movement, interpolated remote players, server-side scoring, and a single fire RPC with lag-compensated hit detection.

## Setup (10 min)

1. New Unity 6 project. Install packages:
   - `com.unity.netcode.gameobjects` (2.x)
   - `com.unity.transport`
2. Create a `MultiplayerBootstrap` scene with:
   - Empty GameObject `NetworkManager` with `NetworkManager` + `UnityTransport` components.
   - `UnityTransport.ConnectionData.Port = 7777`.
3. Open `ProjectSettings > Player > Other Settings > Active Build Settings`. Add a scene reference for Bootstrap.
4. Create an empty scene `GameScene` for actual play.

## Part A: Player prefab (15 min)

1. Capsule primitive. Add `NetworkObject`, `NetworkTransform` (Interpolation = Interpolate, Snap = true, Client Authoritative = false).
2. Add `PlayerMotor` script.
3. Add `PlayerInput` script.

`PlayerMotor.cs`:
```csharp
using Unity.Netcode;
using UnityEngine;

public class PlayerMotor : NetworkBehaviour
{
    [SerializeField] float moveSpeed = 5f;
    [SerializeField] float yawSpeed = 180f;

    [Rpc(SendTo.Server, Delivery = RpcDelivery.Unreliable)]
    public void SubmitInputRpc(Vector2 move, float yaw, double clientTime, RpcParams p = default)
    {
        if (p.Receive.SenderClientId != OwnerClientId) return;
        var fwd = Quaternion.Euler(0, yaw, 0) * Vector3.forward;
        var delta = (fwd * move.y + Vector3.right * move.x) * moveSpeed * Time.fixedDeltaTime;
        transform.position += delta;
        _lastServerPos = transform.position;
        _lastServerTick = NetworkManager.ServerTime.Tick;
    }

    public Vector3 _lastServerPos;
    public uint _lastServerTick;

    public override void OnNetworkSpawn()
    {
        if (IsOwner) SubmitInputRpc(Vector2.zero, transform.eulerAngles.y, 0);
    }
}
```

`PlayerInput.cs`:
```csharp
using Unity.Netcode;
using UnityEngine;

[RequireComponent(typeof(PlayerMotor))]
public class PlayerInput : NetworkBehaviour
{
    PlayerMotor _motor;
    float _yaw;

    public override void OnNetworkSpawn()
    {
        _motor = GetComponent<PlayerMotor>();
        if (!IsOwner) { enabled = false; return; }
        _yaw = transform.eulerAngles.y;
    }

    void Update()
    {
        if (!IsOwner) return;
        var move = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
        if (Input.GetKey(KeyCode.Q)) _yaw -= yawSpeed * Time.deltaTime;
        if (Input.GetKey(KeyCode.E)) _yaw += yawSpeed * Time.deltaTime;
        transform.rotation = Quaternion.Euler(0, _yaw, 0);
        _motor.SubmitInputRpc(move, _yaw, NetworkManager.LocalTime.Time);
    }
}
```

Set the capsule as the player prefab. In `NetworkManager.PlayerPrefab`, assign this. Place it in `Resources/` or add to NetworkPrefabs list directly.

## Part B: Host and client startup UI (10 min)

`MultiplayerMenu.cs`:
```csharp
using Unity.Netcode;
using UnityEngine;
using UnityEngine.UI;

public class MultiplayerMenu : MonoBehaviour
{
    [SerializeField] InputField ipField;
    [SerializeField] InputField portField;
    [SerializeField] Text status;

    public void StartHost()
    {
        Configure();
        if (!NetworkManager.Singleton.StartHost()) SetStatus("Host failed");
    }

    public void StartClient()
    {
        Configure();
        if (!NetworkManager.Singleton.StartClient()) SetStatus("Connect failed");
    }

    public void StartServer()
    {
        Configure();
        if (!NetworkManager.Singleton.StartServer()) SetStatus("Server failed");
    }

    void Configure()
    {
        var t = NetworkManager.Singleton.GetComponent<Unity.Netcode.Transports.UTP.UnityTransport>();
        t.SetConnectionData(ipField.text, ushort.Parse(portField.text));
    }

    void SetStatus(string s) => status.text = s;
}
```

Wire three buttons. Run two builds: one as host, one as client. Press host, then client. Both should see two capsules.

## Part C: Server-side validation and scoring (10 min)

`MatchScore.cs`:
```csharp
using Unity.Netcode;
using UnityEngine;

public class MatchScore : NetworkBehaviour
{
    public NetworkVariable<int> RedScore = new(0);
    public NetworkVariable<int> BlueScore = new(0);

    public override void OnNetworkSpawn()
    {
        if (!IsServer) return;
        RedScore.OnValueChanged += (_, v) => Debug.Log($"Red: {v}");
        BlueScore.OnValueChanged += (_, v) => Debug.Log($"Blue: {v}");
    }
}
```

Add a NetworkObject with this script to the GameScene. Mark `AlwaysReplicateAsRoot` so it spawns on both ends.

## Part D: Lag-compensated fire RPC (20 min)

`HitscanWeapon.cs`:
```csharp
using System.Collections.Generic;
using Unity.Netcode;
using UnityEngine;

public class HitscanWeapon : NetworkBehaviour
{
    [SerializeField] float maxDistance = 50f;
    [SerializeField] int damage = 25;

    public struct PlayerSnapshot
    {
        public uint Tick;
        public Vector3 Position;
    }

    // server: per-client history (one entry per server tick)
    readonly Dictionary<ulong, Queue<PlayerSnapshot>> _history = new();
    const int HistorySize = 128;

    [Rpc(SendTo.Server, Delivery = RpcDelivery.Unreliable)]
    public void FireRpc(Vector3 origin, Vector3 direction, double clientTime, RpcParams p = default)
    {
        if (p.Receive.SenderClientId != OwnerClientId) return;
        var shooterId = p.Receive.SenderClientId;
        var tick = NetworkManager.ServerTime.TickAtTime(clientTime);
        var rewindOrigin = PositionAt(shooterId, tick);
        var rewindDir = direction;
        if (Physics.Raycast(rewindOrigin, rewindDir, out var hit, maxDistance))
        {
            var target = hit.collider.GetComponent<NetworkObject>();
            if (target != null && target.OwnerClientId != shooterId)
                ApplyDamageRpc(target.OwnerClientId, damage, RpcTarget.Single(target.OwnerClientId, RpcTargetUse.Temp));
        }
    }

    Vector3 PositionAt(ulong clientId, uint tick)
    {
        if (!_history.TryGetValue(clientId, out var q)) return transform.position;
        foreach (var snap in q)
            if (snap.Tick == tick) return snap.Position;
        return transform.position;
    }

    [Rpc(SendTo.SpecifiedInParams)]
    public void ApplyDamageRpc(ulong target, int amount, RpcParams p)
    {
        // client shows damage indicator
        Debug.Log($"took {amount} damage");
    }

    public void ServerTickRecord()
    {
        // call this from a server-side system each tick for every player
    }
}
```

For a complete implementation, record a snapshot of every player position every server tick into `_history`. Use a fixed-size ring buffer per player (128 entries at 30 Hz = ~4.2 seconds of history). On FireRpc, look up the shooter's position at `clientTime` and use that as the raycast origin.

## Part E: Predict locally (10 min)

Modify `PlayerInput.Update` to apply movement locally **before** sending the RPC:

```csharp
void Update()
{
    if (!IsOwner) return;
    var move = new Vector2(Input.GetAxisRaw("Horizontal"), Input.GetAxisRaw("Vertical"));
    if (Input.GetKey(KeyCode.Q)) _yaw -= yawSpeed * Time.deltaTime;
    if (Input.GetKey(KeyCode.E)) _yaw += yawSpeed * Time.deltaTime;
    transform.rotation = Quaternion.Euler(0, _yaw, 0);

    var fwd = Quaternion.Euler(0, _yaw, 0) * Vector3.forward;
    var predicted = (fwd * move.y + Vector3.right * move.x) * moveSpeed * Time.fixedDeltaTime;
    transform.position += predicted; // client-side prediction

    _motor.SubmitInputRpc(move, _yaw, NetworkManager.LocalTime.Time);
}
```

## Verification

1. Run host, run a second instance as client, see two capsules on each screen.
2. The local capsule (owner) responds instantly to input. The remote capsule (other owner) interpolates smoothly even with `NetworkSimulator` adding 100 ms latency.
3. Open Multiplayer Tools > NetworkSimulator. Add 100 ms RTT. The local player still feels responsive; the remote player is smooth (interpolated) and visibly delayed.
4. Fire RPC: the host's raycast hits the target's rewound position, not their current position. Verify by spawning a moving target and shooting where you see them, not where the server says they are.

## Common pitfalls

- Forgot to drag the player prefab into NetworkManager's PlayerPrefab slot. Symptom: nothing spawns on connection.
- Server and client builds are from different prefab GUIDs. Symptom: spawn fails only in build, works in editor. Fix: keep prefab assets identical across build artifacts.
- Updating a NetworkVariable from a client. The server silently ignores client writes. Symptom: value never changes.
- Calling `Instantiate` without `Spawn`. The object is not networked. Symptom: no replication.
- Subscribing to `OnValueChanged` in `Start` instead of `OnNetworkSpawn`. The event fires before subscription. Symptom: missing the first value change.
- Reading `transform.position` on the host for the owner and the network transform for everyone else. Pick one. The host should treat the owner as authoritative for prediction but the server is still the authority for everyone else.

## Stretch goals

- Replace the input with a command pattern from module 14.
- Add interest management: only replicate other players within 50 m.
- Move the simulation to DOTS using Netcode for Entities. Module 9 stretch.

## What we're testing

- Can you configure NetworkManager, UnityTransport, and start host/client?
- Do you understand the difference between server authority and client authority?
- Can you implement a server-validated RPC with identity, preconditions, and effect?
- Do you know when to predict locally vs interpolate remotely?
