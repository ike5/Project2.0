using UnityEngine;
using UnityEngine.SceneManagement;

// Challenge 12 reference: GameManager with win/lose, a countdown timer, and restart.
// Replace your GameManager with this (and add a Hazard script — see solution.md).
public class GameManagerExtended : MonoBehaviour
{
    public static GameManagerExtended Instance { get; private set; }

    [SerializeField] private GameSettings settings;      // coinsToWin, etc.
    [SerializeField] private HudController hud;
    [SerializeField] private float timeLimit = 30f;
    [SerializeField] private MonoBehaviour playerMovement; // assign PlayerMovement2D to disable on end

    private int _score;
    private int _coins;
    private float _timeLeft;
    private bool _gameOver;

    private void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
        _timeLeft = timeLimit;
    }

    private void Update()
    {
        if (_gameOver) return;

        _timeLeft -= Time.deltaTime;
        hud?.SetTimer(Mathf.CeilToInt(_timeLeft));
        if (_timeLeft <= 0f) Lose("Time's up!");
    }

    public void AddScore(int amount)
    {
        if (_gameOver) return;
        _score += amount;
        _coins++;
        hud?.SetScore(_score);

        int needed = settings != null ? settings.coinsToWin : 5;
        if (_coins >= needed) Win();
    }

    private void Win() => End("You Win!");
    public void Lose(string reason) => End(reason);

    private void End(string message)
    {
        _gameOver = true;
        hud?.ShowMessage(message);
        if (playerMovement != null) playerMovement.enabled = false;   // stop the player
        Invoke(nameof(Restart), 2f);
    }

    public void Restart() => SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex);
}
