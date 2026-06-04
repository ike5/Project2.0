using UnityEngine;

// Module 13: a 3D collectible. Uses a trigger Collider (Is Trigger) and OnTriggerEnter
// (the 3D variant, no "2D" suffix). Plays a sound and reports to the manager.
public class PickUp3D : MonoBehaviour
{
    [SerializeField] private int value = 1;
    [SerializeField] private AudioClip pickupSound;

    private void OnTriggerEnter(Collider other)
    {
        if (!other.CompareTag("Player")) return;

        if (pickupSound != null)
            AudioSource.PlayClipAtPoint(pickupSound, transform.position);

        Game3DManager.Instance?.Collect(value);
        Destroy(gameObject);
    }
}
