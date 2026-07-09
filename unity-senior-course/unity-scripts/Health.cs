// Module 01 — Assets folder + asmdef + Health component
// The minimum senior-grade starting point for a Unity project.

using System;
using UnityEngine;

namespace MyGame.Player
{
    [Serializable]
    public struct HealthData
    {
        public int Max;
        public int Current;
    }

    [DisallowMultipleComponent]
    public class Health : MonoBehaviour
    {
        [SerializeField] HealthData _data = new() { Max = 100, Current = 100 };

        public int Max => _data.Max;
        public int Current => Mathf.Max(0, _data.Current);
        public bool IsDead => Current == 0;

        public event Action<int> Damaged;
        public event Action<int> Healed;
        public event Action Died;

        public void TakeDamage(int amount)
        {
            if (amount <= 0 || IsDead) return;
            int before = _data.Current;
            int after = Mathf.Max(0, before - amount);
            int delta = before - after;
            _data.Current = after;
            Damaged?.Invoke(delta);
            if (IsDead) Died?.Invoke();
        }

        public void Heal(int amount)
        {
            if (amount <= 0 || IsDead) return;
            int before = _data.Current;
            int after = Mathf.Min(_data.Max, before + amount);
            int diff = after - before;
            _data.Current = after;
            Healed?.Invoke(diff);
        }
    }
}
