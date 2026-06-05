using UnityEngine;

// Module 11: move a GameObject directly via its Transform (no physics yet).
// Demonstrates Update, Input, Time.deltaTime, and [SerializeField] tuning.
public class TransformMover : MonoBehaviour
{
    [SerializeField] private float speed = 5f;   // units per second; tune in the Inspector

    private void Update()
    {
        // Read input as a -1..1 axis (arrow keys / A,D / W,S by default).
        float h = Input.GetAxisRaw("Horizontal");
        float v = Input.GetAxisRaw("Vertical");

        var direction = new Vector3(h, v, 0f).normalized;

        // Multiply by Time.deltaTime so movement is frame-rate independent:
        // "speed units per second", not "speed units per frame".
        transform.position += direction * (speed * Time.deltaTime);
    }
}
