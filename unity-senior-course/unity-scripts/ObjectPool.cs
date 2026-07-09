// Module 14 — Senior patterns: pool + service locator + event bus
// The combination pattern for runtime systems.

using System;
using System.Collections.Generic;
using UnityEngine;

namespace MyGame.Infrastructure
{
    /// <summary>
    /// Generic object pool. Pre-allocates, recycles, no allocations
    /// on Get/Return after warmup.
    /// </summary>
    public class ObjectPool<T> where T : Component
    {
        readonly T _prefab;
        readonly Transform _parent;
        readonly Stack<T> _available;
        readonly HashSet<T> _inUse;
        readonly Action<T> _onGet;
        readonly Action<T> _onReturn;

        public int CountInactive => _available.Count;
        public int CountActive => _inUse.Count;
        public int CountAll => _available.Count + _inUse.Count;

        public ObjectPool(
            T prefab,
            int initialSize,
            Transform parent = null,
            Action<T> onGet = null,
            Action<T> onReturn = null)
        {
            _prefab = prefab;
            _parent = parent;
            _available = new Stack<T>(initialSize);
            _inUse = new HashSet<T>();
            _onGet = onGet;
            _onReturn = onReturn;

            for (int i = 0; i < initialSize; i++)
            {
                var instance = UnityEngine.Object.Instantiate(_prefab, _parent);
                instance.gameObject.SetActive(false);
                _available.Push(instance);
            }
        }

        public T Get()
        {
            T instance;
            if (_available.Count > 0)
            {
                instance = _available.Pop();
            }
            else
            {
                instance = UnityEngine.Object.Instantiate(_prefab, _parent);
            }
            _inUse.Add(instance);
            instance.gameObject.SetActive(true);
            _onGet?.Invoke(instance);
            return instance;
        }

        public void Return(T instance)
        {
            if (!_inUse.Remove(instance)) return;
            _onReturn?.Invoke(instance);
            instance.gameObject.SetActive(false);
            if (_parent != null) instance.transform.SetParent(_parent, false);
            _available.Push(instance);
        }

        public void Clear()
        {
            foreach (var t in _inUse)
            {
                if (t != null) UnityEngine.Object.Destroy(t.gameObject);
            }
            while (_available.Count > 0)
            {
                var t = _available.Pop();
                if (t != null) UnityEngine.Object.Destroy(t.gameObject);
            }
            _inUse.Clear();
        }
    }

    /// <summary>
    /// Typed event bus. Replaces direct references between systems.
    /// </summary>
    public class EventBus<T> where T : class
    {
        readonly List<Action<T>> _listeners = new(8);

        public void Subscribe(Action<T> listener)
        {
            if (listener != null && !_listeners.Contains(listener))
                _listeners.Add(listener);
        }

        public void Unsubscribe(Action<T> listener) => _listeners.Remove(listener);

        public void Publish(T evt)
        {
            for (int i = _listeners.Count - 1; i >= 0; i--)
            {
                try { _listeners[i].Invoke(evt); }
                catch (Exception e) { Debug.LogException(e); }
            }
        }
    }
}
