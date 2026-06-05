using UnityEngine;
using UnityEngine.SceneManagement;

// Module 12: tracks score and win state. A very simple singleton so other scripts
// (like Coin) can reach it via GameManager.Instance.
public class GameManager : MonoBehaviour
{
    public static GameManager Instance { get; private set; }

    [SerializeField] private int coinsToWin = 5;
    [SerializeField] private HudController hud;   // assign in the Inspector

    private int _score;
    private int _coinsCollected;

    private void Awake()
    {
        // Basic singleton: keep the first instance, destroy duplicates.
        if (Instance != null && Instance != this)
        {
            Destroy(gameObject);
            return;
        }
        Instance = this;
    }

    private void Start()
    {
        UpdateHud();
    }

    public void AddScore(int amount)
    {
        _score += amount;
        _coinsCollected++;
        UpdateHud();

        if (_coinsCollected >= coinsToWin)
            Win();
    }

    private void Win()
    {
        Debug.Log($"You win! Final score: {_score}");
        if (hud != null) hud.ShowMessage("You Win!");
        // Optional: reload the scene after a moment, or load a "win" scene.
        // Invoke(nameof(Restart), 2f);
    }

    public void Restart() => SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);

    private void UpdateHud()
    {
        if (hud != null) hud.SetScore(_score);
    }
}
