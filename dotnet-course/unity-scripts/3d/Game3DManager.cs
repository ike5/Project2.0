using UnityEngine;

// Module 13: minimal 3D game manager — counts pickups, updates the HUD, plays a sound
// on win, and can switch scenes.
public class Game3DManager : MonoBehaviour
{
    public static Game3DManager Instance { get; private set; }

    [SerializeField] private int countToWin = 8;
    [SerializeField] private HudController hud;       // reuse the 2D HUD script
    [SerializeField] private AudioSource musicSource; // optional background music
    [SerializeField] private AudioClip winSound;

    private int _count;

    private void Awake()
    {
        if (Instance != null && Instance != this) { Destroy(gameObject); return; }
        Instance = this;
    }

    private void Start()
    {
        hud?.SetScore(0);
        if (musicSource != null) musicSource.Play();
    }

    public void Collect(int value)
    {
        _count += value;
        hud?.SetScore(_count);
        if (_count >= countToWin) Win();
    }

    private void Win()
    {
        hud?.ShowMessage("You Win!");
        if (winSound != null && musicSource != null)
            musicSource.PlayOneShot(winSound);
        Debug.Log("3D level complete!");
    }
}
