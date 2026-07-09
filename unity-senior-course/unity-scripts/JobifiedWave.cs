// Module 05 — Native containers + Job + Burst
// The pattern for hot-path gameplay code.

using Unity.Burst;
using Unity.Collections;
using Unity.Jobs;
using Unity.Mathematics;
using UnityEngine;

public class JobifiedWave : MonoBehaviour
{
    [SerializeField] int _count = 10_000;
    [SerializeField] float _amplitude = 1f;
    [SerializeField] float _frequency = 1f;

    NativeArray<float3> _positions;
    NativeArray<float4x4> _matrices;
    JobHandle _handle;
    bool _initialized;

    void OnEnable()
    {
        _positions = new NativeArray<float3>(_count, Allocator.Persistent);
        _matrices = new NativeArray<float4x4>(_count, Allocator.Persistent);

        for (int i = 0; i < _count; i++)
        {
            _positions[i] = new float3(
                (i % 100) * 0.5f,
                0f,
                (i / 100) * 0.5f);
        }
        _initialized = true;
    }

    void OnDisable()
    {
        _handle.Complete();
        if (_positions.IsCreated) _positions.Dispose();
        if (_matrices.IsCreated) _matrices.Dispose();
    }

    void Update()
    {
        if (!_initialized) return;

        _handle.Complete();  // wait for previous frame's job

        var job = new WaveJob
        {
            Positions = _positions,
            Matrices = _matrices,
            Time = Time.time,
            DeltaTime = Time.deltaTime,
            Amplitude = _amplitude,
            Frequency = _frequency
        };
        _handle = job.Schedule(_count, 64);
    }

    [BurstCompile]
    struct WaveJob : IJobParallelFor
    {
        public NativeArray<float3> Positions;
        [WriteOnly] public NativeArray<float4x4> Matrices;
        public float Time;
        public float DeltaTime;
        public float Amplitude;
        public float Frequency;

        public void Execute(int index)
        {
            var p = Positions[index];
            p.y = math.sin(Time * Frequency + index * 0.01f) * Amplitude;
            Positions[index] = p;

            Matrices[index] = float4x4.Translate(p);
        }
    }
}
