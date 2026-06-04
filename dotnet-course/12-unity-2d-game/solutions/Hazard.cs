using UnityEngine;

// Challenge 12, task 1: a hazard that ends the game when the player touches it.
// Put a trigger Collider2D on the GameObject and tag the player "Player".
public class Hazard : MonoBehaviour
{
    private void OnTriggerEnter2D(Collider2D other)
    {
        if (other.CompareTag("Player"))
            GameManagerExtended.Instance?.Lose("Game Over");
    }
}
