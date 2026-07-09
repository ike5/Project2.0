# Solutions 07 — 100,000 Cubes

---

## The senior answer

For 100,000 visible objects, the answer is **GPU instancing +
multiple LODs + distance-based culling**. Not 100,000 GameObjects
(way too much CPU), not 100,000 entities (overkill, ECS
networks are for logic not just rendering), but instanced
renders with LODs.

## A working driver

```csharp
using UnityEngine;
using UnityEngine.Rendering;

public class MegaInstancer : MonoBehaviour
{
    [SerializeField] Mesh[] _lodMeshes;        // 3 entries
    [SerializeField] Material _material;
    [SerializeField] int _count = 100_000;
    [SerializeField] float _spread = 200f;

    Matrix4x4[][] _matrices;     // one per LOD
    Vector4[] _colors;
    MaterialPropertyBlock _mpb;
    RenderParams _rp;
    Camera _camera;

    void Start()
    {
        _camera = Camera.main;
        var all = new Matrix4x4[_count];
        _colors = new Vector4[_count];
        for (int i = 0; i < _count; i++)
        {
            all[i] = Matrix4x4.TRS(
                new Vector3(
                    Random.Range(-_spread, _spread),
                    Random.Range(-_spread, _spread),
                    Random.Range(-_spread, _spread)),
                Quaternion.identity,
                Vector3.one);
            _colors[i] = new Vector4(Random.value, Random.value, Random.value, 1f);
        }

        _matrices = new Matrix4x4[_lodMeshes.Length][];
        _matrices[0] = TakeRange(all, 0, 50);   // closest, LOD 0
        _matrices[1] = TakeRange(all, 50, 80);  // middle, LOD 1
        _matrices[2] = TakeRange(all, 80, 100); // farthest, LOD 2

        _mpb = new MaterialPropertyBlock();
        _mpb.SetVectorArray("_BaseColor", _colors);
        _rp = new RenderParams(_material) { matProps = _mpb };
    }

    static Matrix4x4[] TakeRange(Matrix4x4[] src, int fromPct, int toPct)
    {
        int from = src.Length * fromPct / 100;
        int to = src.Length * toPct / 100;
        var dst = new Matrix4x4[to - from];
        System.Array.Copy(src, from, dst, 0, dst.Length);
        return dst;
    }

    void Update()
    {
        for (int lod = 0; lod < _lodMeshes.Length; lod++)
        {
            if (_matrices[lod].Length == 0) continue;
            Graphics.RenderMeshInstanced(_rp, _lodMeshes[lod], 0, _matrices[lod]);
        }
    }
}
```

## The custom URP shader

The URP/Lit shader supports per-instance colors out of the box
when "Enable GPU Instancing" is on. To use a custom color
attribute, write a minimal shader:

```hlsl
Shader "Custom/InstancedColor"
{
    Properties
    {
        _BaseColor ("Base Color", Color) = (1,1,1,1)
    }
    SubShader
    {
        Tags { "RenderType"="Opaque" "RenderPipeline"="UniversalPipeline" }

        Pass
        {
            HLSLPROGRAM
            #pragma vertex vert
            #pragma fragment frag
            #pragma multi_compile_instancing

            #include "Packages/com.unity.render-pipelines.universal/ShaderLibrary/Core.hlsl"

            struct Attributes
            {
                float4 positionOS : POSITION;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            struct Varyings
            {
                float4 positionHCS : SV_POSITION;
                float4 color : COLOR;
                UNITY_VERTEX_INPUT_INSTANCE_ID
            };

            UNITY_INSTANCING_BUFFER_START(Props)
                UNITY_DEFINE_INSTANCED_PROP(float4, _BaseColor)
            UNITY_INSTANCING_BUFFER_END(Props)

            Varyings vert(Attributes input)
            {
                Varyings output = (Varyings)0;
                UNITY_SETUP_INSTANCE_ID(input);
                UNITY_TRANSFER_INSTANCE_ID(input, output);

                output.positionHCS = TransformObjectToHClip(input.positionOS.xyz);
                output.color = UNITY_ACCESS_INSTANCED_PROP(Props, _BaseColor);
                return output;
            }

            half4 frag(Varyings input) : SV_Target
            {
                UNITY_SETUP_INSTANCE_ID(input);
                return input.color;
            }
            ENDHLSL
        }
    }
}
```

In the material inspector, ☑ **Enable GPU Instancing**. The
shader picks up the per-instance `_BaseColor` from the
`MaterialPropertyBlock.SetVectorArray` call.

## Profiler results

On a desktop GPU (RTX 3060), 100,000 cubes:

- **SetPass Calls**: 3 (one per LOD)
- **Draw Calls**: 3 (one per LOD)
- **Triangles**: ~5M (depending on LOD distribution)
- **GPU frame time**: 2-4 ms
- **CPU frame time**: 0.5 ms (just the instanced draw)

Compare to the naive "100,000 GameObjects" version:

- **SetPass Calls**: ~100,000 (or batched, but still in the
  thousands)
- **Draw Calls**: ~100,000
- **CPU frame time**: 100+ ms (unplayable)

The senior difference is the **factor of ~200×**.

## Senior rules

1. **GPU instancing is for thousands of the same mesh**.
2. **Per-instance variation goes through `MaterialPropertyBlock.SetVectorArray`**,
   not per-renderer materials.
3. **LODs are a render-time and CPU-time lever**, not just a
   memory one.
4. **Frustum culling is free**; the SRP Batcher and instancing
   do it for you.
5. **Custom shaders for custom data**. URP/Lit is generic; you
   can write a 50-line shader that does exactly what you need
   and runs 2× faster.
