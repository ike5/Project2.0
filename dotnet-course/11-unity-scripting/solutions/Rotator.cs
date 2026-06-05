using UnityEngine;

// Challenge 11, task 2: spin this GameObject around Z at a tunable speed.
public class Rotator : MonoBehaviour
{
    [SerializeField] private float degreesPerSecond = 180f;

    private void Update()
    {
        // Rotate around the Z axis, frame-rate independent.
        transform.Rotate(0f, 0f, degreesPerSecond * Time.deltaTime);
    }
}
