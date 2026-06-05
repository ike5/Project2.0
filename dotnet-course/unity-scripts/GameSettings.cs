using UnityEngine;

// Module 11: a ScriptableObject — a data container asset, decoupled from any scene.
// Create instances via the editor: Assets -> Create -> MiniGame -> Game Settings.
// Reference one from your MonoBehaviours via a [SerializeField] field.
[CreateAssetMenu(fileName = "GameSettings", menuName = "MiniGame/Game Settings")]
public class GameSettings : ScriptableObject
{
    [Header("Player")]
    public float moveSpeed = 5f;

    [Header("Scoring")]
    public int coinValue = 10;
    public int coinsToWin = 5;

    [Header("Spawning")]
    public float spawnInterval = 1.5f;
}
