using UnityEngine;

// Attach this to a GameObject named exactly "SceneBridge" in your Unity scene.
// Native code drives it with:
//   sendMessageToGOWithName("SceneBridge", "SetColor", "1,0,0")
//   sendMessageToGOWithName("SceneBridge", "Spawn", "")
//
// Methods called via sendMessage MUST be public and take a single string parameter
// (or no parameter). Unity passes the message string straight through.
public class SceneBridge : MonoBehaviour
{
    [SerializeField] private Renderer targetRenderer;   // assign the cube's Renderer
    [SerializeField] private GameObject spawnPrefab;    // optional: something to spawn

    private int score;

    // native -> Unity: set the target's color from "r,g,b" (0..1 each).
    public void SetColor(string rgb)
    {
        var parts = rgb.Split(',');
        if (parts.Length == 3 &&
            float.TryParse(parts[0], out var r) &&
            float.TryParse(parts[1], out var g) &&
            float.TryParse(parts[2], out var b) &&
            targetRenderer != null)
        {
            targetRenderer.material.color = new Color(r, g, b);
        }
    }

    // native -> Unity: spawn something, then report the new score back to native.
    public void Spawn(string _)
    {
        if (spawnPrefab != null)
        {
            var pos = new Vector3(Random.Range(-2f, 2f), Random.Range(0f, 3f), 0f);
            Instantiate(spawnPrefab, pos, Quaternion.identity);
        }
        score++;
        NativeAPI.SendScore(score);                     // Unity -> native
    }

    // Example of pushing a status string out to native (Unity -> native).
    private void Start()
    {
        NativeAPI.SendMessage("Unity scene ready");
    }
}
