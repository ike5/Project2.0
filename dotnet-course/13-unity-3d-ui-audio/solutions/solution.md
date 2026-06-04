# Challenge 13 — Reference Notes

### 1. Main menu
```csharp
using UnityEngine;
using UnityEngine.SceneManagement;
public class MainMenu : MonoBehaviour
{
    public void StartGame() => SceneManager.LoadScene("Main");
    public void Quit()
    {
        Application.Quit();                     // no-op in the editor
#if UNITY_EDITOR
        UnityEditor.EditorApplication.isPlaying = false;   // stops Play mode in-editor
#endif
    }
}
```
Add `Menu` as build index 0 (drag it to the top of **Build Settings → Scenes In Build**).

### 2. Persistent score
**PlayerPrefs (simplest):**
```csharp
PlayerPrefs.SetInt("FinalScore", _count);     // in Win()
// in the Win scene:
int score = PlayerPrefs.GetInt("FinalScore", 0);
```
**DontDestroyOnLoad manager (no disk):**
```csharp
void Awake()
{
    if (Instance != null) { Destroy(gameObject); return; }
    Instance = this;
    DontDestroyOnLoad(gameObject);   // survives scene loads
}
```

### 3. Pause
```csharp
private bool _paused;
void Update()
{
    if (Input.GetKeyDown(KeyCode.Escape))
    {
        _paused = !_paused;
        Time.timeScale = _paused ? 0f : 1f;
        pausePanel.SetActive(_paused);
    }
}
```
> `Time.timeScale = 0` makes `Time.deltaTime` 0, so `Update` still runs (UI works) but
> time-based motion stops, and **`FixedUpdate` stops firing** (physics is paused).
> Don't drive UI animations with scaled time while paused — use `unscaledDeltaTime`.

### 4. Walls + fall detection
- Surround the ground with elongated **Cubes** (solid colliders).
- In `BallController` or the manager:
  ```csharp
  void Update() { if (transform.position.y < -5f) SceneManager.LoadScene(SceneManager.GetActiveScene().buildIndex); }
  ```

### 5. Audio mixer (stretch)
- Create an **AudioMixer** (Project → Create → Audio Mixer), add a **Master** group,
  expose its volume parameter (right-click → Expose).
- Route AudioSources to the mixer group; set volume from a slider:
  ```csharp
  mixer.SetFloat("MasterVol", Mathf.Log10(value) * 20);   // linear slider -> dB
  ```
