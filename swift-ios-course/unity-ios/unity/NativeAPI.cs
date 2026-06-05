using System.Runtime.InteropServices;
using UnityEngine;

// Unity (C#) -> native. The [DllImport("__Internal")] functions are implemented in the
// native app's NativeCallsPlugin.mm. In the Editor (or non-iOS) we no-op with a log so
// the same code runs everywhere.
public static class NativeAPI
{
#if UNITY_IOS && !UNITY_EDITOR
    [DllImport("__Internal")]
    private static extern void native_sendScore(int score);

    [DllImport("__Internal")]
    private static extern void native_sendMessage(string message);
#endif

    public static void SendScore(int score)
    {
#if UNITY_IOS && !UNITY_EDITOR
        native_sendScore(score);
#else
        Debug.Log($"[NativeAPI] SendScore({score}) — editor no-op");
#endif
    }

    public static void SendMessage(string message)
    {
#if UNITY_IOS && !UNITY_EDITOR
        native_sendMessage(message);
#else
        Debug.Log($"[NativeAPI] SendMessage(\"{message}\") — editor no-op");
#endif
    }
}
