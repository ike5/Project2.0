using UnityEngine;
using TMPro;   // TextMeshPro: Unity's standard text. Import "TMP Essentials" when prompted.

// Module 12/13: updates on-screen text. Attach to a GameObject and wire the two
// TextMeshProUGUI references (a score label and a centered message label).
public class HudController : MonoBehaviour
{
    [SerializeField] private TMP_Text scoreText;
    [SerializeField] private TMP_Text messageText;
    [SerializeField] private TMP_Text timerText;   // optional (Challenge 12)

    private void Start()
    {
        if (messageText != null) messageText.text = "";   // hidden until we win/lose
    }

    public void SetScore(int score)
    {
        if (scoreText != null) scoreText.text = $"Score: {score}";
    }

    public void SetTimer(int secondsLeft)
    {
        if (timerText != null) timerText.text = $"Time: {secondsLeft}";
    }

    public void ShowMessage(string message)
    {
        if (messageText != null) messageText.text = message;
    }
}
