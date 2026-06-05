using UnityEngine;

// Module 12: a collectible. Its Collider2D is set to "Is Trigger", so when the player
// overlaps it, OnTriggerEnter2D fires — we add score and remove the coin.
public class Coin : MonoBehaviour
{
    [SerializeField] private int value = 10;

    private void OnTriggerEnter2D(Collider2D other)
    {
        // Only react to the player (tag the player GameObject "Player" in the Inspector).
        if (!other.CompareTag("Player")) return;

        // Find the game manager and report the pickup.
        GameManager.Instance?.AddScore(value);

        Destroy(gameObject);   // remove this coin from the scene
    }
}
