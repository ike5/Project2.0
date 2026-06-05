using UnityEngine;

// Module 13: classic "roll-a-ball" — move a sphere with physics forces in 3D.
[RequireComponent(typeof(Rigidbody))]
public class BallController : MonoBehaviour
{
    [SerializeField] private float force = 10f;

    private Rigidbody _rb;
    private Vector3 _input;

    private void Awake() => _rb = GetComponent<Rigidbody>();

    private void Update()
    {
        // X/Z plane movement (Y is up in 3D). Sample input each frame.
        _input = new Vector3(
            Input.GetAxisRaw("Horizontal"),
            0f,
            Input.GetAxisRaw("Vertical"));
    }

    private void FixedUpdate()
    {
        // Apply force on the physics step; the Rigidbody handles gravity & collisions.
        _rb.AddForce(_input.normalized * force);
    }
}
