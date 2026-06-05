using UnityEngine;

// Module 12: physics-based 2D movement using Rigidbody2D.
// Read input in Update; apply movement in FixedUpdate (the physics step).
[RequireComponent(typeof(Rigidbody2D))]   // auto-adds a Rigidbody2D if missing
public class PlayerMovement2D : MonoBehaviour
{
    [SerializeField] private float speed = 6f;

    private Rigidbody2D _rb;
    private Vector2 _input;

    private void Awake()
    {
        // Cache the component reference once (don't GetComponent every frame).
        _rb = GetComponent<Rigidbody2D>();
    }

    private void Update()
    {
        // Sample input every frame...
        _input = new Vector2(
            Input.GetAxisRaw("Horizontal"),
            Input.GetAxisRaw("Vertical")).normalized;
    }

    private void FixedUpdate()
    {
        // ...but move the body on the physics clock for stable collisions.
        _rb.MovePosition(_rb.position + _input * (speed * Time.fixedDeltaTime));
    }
}
