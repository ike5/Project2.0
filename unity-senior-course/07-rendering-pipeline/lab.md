# Lab 07 — Rendering: URP, SRP Batcher, GPU Instancing

A hands-on session with the rendering tools.

**Time**: 90 minutes.

---

## Step 1 — Set up the test scene

1. Open `UnitySeniorLab`. Open a new scene.
2. Add 1,000 cubes in a 10×10×10 grid. Use a small
   `CubeSpawner` script:

   ```csharp
   using UnityEngine;

   public class CubeSpawner : MonoBehaviour
   {
       [SerializeField] GameObject _prefab;
       [SerializeField] int _count = 1000;
       [SerializeField] float _spacing = 1.5f;

       void Start()
       {
           int side = Mathf.CeilToInt(Mathf.Pow(_count, 1f / 3f));
           for (int x = 0; x < side; x++)
           for (int y = 0; y < side; y++)
           for (int z = 0; z < side; z++)
           {
               var pos = new Vector3(
                   (x - side / 2) * _spacing,
                   (y - side / 2) * _spacing,
                   (z - side / 2) * _spacing);
               Instantiate(_prefab, pos, Quaternion.identity, transform);
           }
       }
   }
   ```

3. All cubes share one material (`M_Cube`).

## Step 2 — Look at the SRP Batcher

1. **Window → Analysis → Frame Debugger**.
2. Click **Enable**.
3. Click a frame.
4. In the left pane, expand **RenderLoop.Draw → ...** and look
   for the cube draws.
5. For each, the right pane shows "**SRP Batcher: compatible**"
   or "incompatible".

**Senior observation**: 1,000 cubes, 1 material = **1 SetPass
call**, **1 Draw call** (or very few). The SRP Batcher is
batching everything.

## Step 3 — Break the SRP Batcher

Make the cubes use **different materials**:

```csharp
[SerializeField] Material[] _materials;

void Start()
{
    // ...
    for (int x = 0; x < side; x++)
    for (int y = 0; y < side; y++)
    for (int z = 0; z < side; z++)
    {
        var pos = new Vector3(/* ... */);
        var go = Instantiate(_prefab, pos, Quaternion.identity, transform);
        go.GetComponent<MeshRenderer>().material = _materials[(x + y + z) % _materials.Length];
    }
}
```

Create 5 different materials. Re-run.

**Senior observation**: SetPass jumps to 5. Draw calls jump to
1,000. CPU rendering time increases 2-5×.

## Step 4 — Fix it with a material property block

```csharp
[SerializeField] Material _sharedMaterial;
[SerializeField] Color[] _tints;

void Start()
{
    var mpb = new MaterialPropertyBlock();
    for (/* ... */)
    {
        var go = Instantiate(_prefab, pos, Quaternion.identity, transform);
        mpb.SetColor("_BaseColor", _tints[(x + y + z) % _tints.Length]);
        go.GetComponent<MeshRenderer>().SetPropertyBlock(mpb);
    }
}
```

Re-run. SetPass back to 1, Draw calls back to 1,000. **The
senior pattern: one shared material, vary per-renderer with
`MaterialPropertyBlock`.**

## Step 5 — GPU Instancing

Replace the loop with `Graphics.RenderMeshInstanced`:

```csharp
using UnityEngine;
using UnityEngine.Rendering;

public class InstancedCubes : MonoBehaviour
{
    [SerializeField] Mesh _mesh;
    [SerializeField] Material _material;
    [SerializeField] int _count = 10000;
    [SerializeField] float _spread = 50f;

    Matrix4x4[] _matrices;
    MaterialPropertyBlock _mpb;
    RenderParams _rp;

    void Start()
    {
        _matrices = new Matrix4x4[_count];
        for (int i = 0; i < _count; i++)
        {
            _matrices[i] = Matrix4x4.TRS(
                new Vector3(
                    Random.Range(-_spread, _spread),
                    Random.Range(-_spread, _spread),
                    Random.Range(-_spread, _spread)),
                Quaternion.identity,
                Vector3.one);
        }

        _mpb = new MaterialPropertyBlock();
        _mpb.SetColor("_BaseColor", Color.red);

        _rp = new RenderParams(_material)
        {
            matProps = _mpb,
            receiveShadows = true,
            shadowCastingMode = ShadowCastingMode.On
        };
    }

    void Update()
    {
        Graphics.RenderMeshInstanced(_rp, _mesh, 0, _matrices, _count);
    }
}
```

**Material setup**: open the material, ☑ **Enable GPU
Instancing** in the inspector. The shader must be instancing-
compatible (URP/Lit is by default).

Re-run. Look at the Profiler. **SetPass: 1, DrawCalls: 1, but
10000 visible cubes.** The senior way to do "thousands of the
same thing".

## Step 6 — LODs

1. Create three cubes: high-poly (1k tris), medium (250 tris),
   low (50 tris). Save as `Cube_LOD0`, `Cube_LOD1`, `Cube_LOD2`.
2. Add a `LODGroup` component to a GameObject.
3. Assign the three LODs with screen-relative heights:
   - LOD 0: 0.5
   - LOD 1: 0.2
   - LOD 2: 0.05
4. Move the camera in and out. The LOD swaps.

**Senior observation**: with the camera far, the Profiler
shows the lower-tri LOD; the GPU cost drops by 10×.

## Step 7 — Frame Debugger deep-dive

In a scene with 100 cubes, the same material, and a URP/Lit
shader, the Frame Debugger should show:

- 1 SetPass call (the SRP Batcher)
- 100 draws (or batched into a few large ones)
- 1 CBUFFER binding per material

If you see 100 SetPass calls, the SRP Batcher is breaking.
Click on one, look at the right pane for "Batch break reason".

Common reasons:

- Material has more than 16 properties not in `CBUFFER`.
- Shader uses `multi_compile` keywords that don't fold.
- `MaterialPropertyBlock` is used incorrectly.
- The mesh has a non-uniform scale on the parent.

## Stretch goals

- Use `RenderDoc` (free, renderdoc.org) to capture a frame
  and look at the actual draw calls. Compare to the Frame
  Debugger output.
- Add a `LightProbeProxyVolume` for the cubes. The senior
  pattern for "many objects, blended lighting".
- Add a `ReflectionProbe` for the cubes. The senior pattern
  for "many objects, specular reflections".

---

## What you should now understand

- The SRP Batcher is the senior default; check compatibility
  first.
- `MaterialPropertyBlock` is the senior way to vary one or
  two properties without breaking batching.
- GPU Instancing is for thousands of the same mesh.
- LODs are the cheapest 5× you can buy.
- The Frame Debugger is the right tool to verify.
- The Profiler is the right tool to time.
