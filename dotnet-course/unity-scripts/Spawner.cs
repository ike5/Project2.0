using UnityEngine;

// Module 11: instantiate a prefab at random positions, and clean up with Destroy.
// Assign 'prefab' in the Inspector by dragging a prefab asset onto the field.
public class Spawner : MonoBehaviour
{
    [SerializeField] private GameObject prefab;     // a prefab asset to clone
    [SerializeField] private float range = 4f;       // spawn area half-size
    [SerializeField] private float lifetime = 2f;    // seconds before auto-destroy

    private void Update()
    {
        if (Input.GetKeyDown(KeyCode.Space))
            SpawnOne();
    }

    private void SpawnOne()
    {
        if (prefab == null)
        {
            Debug.LogWarning("Spawner: no prefab assigned in the Inspector.");
            return;
        }

        var pos = new Vector3(Random.Range(-range, range), Random.Range(-range, range), 0f);

        // Instantiate creates a new copy of the prefab in the scene at runtime.
        GameObject clone = Instantiate(prefab, pos, Quaternion.identity);

        // Destroy removes it after 'lifetime' seconds (overload with a delay).
        Destroy(clone, lifetime);
    }
}
