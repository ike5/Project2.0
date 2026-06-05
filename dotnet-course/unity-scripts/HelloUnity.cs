using UnityEngine;

// Module 10: your first Unity script. Attach it to any GameObject, press Play, and
// watch the Console. Shows the two most common lifecycle hooks.
public class HelloUnity : MonoBehaviour
{
    // A field marked [SerializeField] shows up in the Inspector for tuning,
    // while staying private in code. (Public fields also show, but prefer this.)
    [SerializeField] private string greeting = "Hello from Unity!";

    // Called once, when the object becomes active (before the first frame).
    private void Start()
    {
        Debug.Log($"{greeting} (from {gameObject.name})");
    }

    // Called every frame. Keep it light; it runs ~60+ times per second.
    private void Update()
    {
        // Log only when the space key is pressed, so we don't spam the Console.
        if (Input.GetKeyDown(KeyCode.Space))
            Debug.Log($"Space pressed at time {Time.time:0.0}s");
    }
}
