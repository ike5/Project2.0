// Objective-C++ plugin: implements the C functions that Unity calls via
// [DllImport("__Internal")]. We forward them to Swift using a registered callback
// (for the score) and NotificationCenter (for string messages).
//
// Add this file to your APP target (not the Unity framework). The function names must
// match the externs in NativeAPI.cs exactly.

#import <Foundation/Foundation.h>

// A C function pointer the Swift side registers to receive score updates.
typedef void (*ScoreHandler)(int);
static ScoreHandler g_scoreHandler = NULL;

#ifdef __cplusplus
extern "C" {
#endif

// Called from Swift to install the score callback.
void RegisterScoreHandler(ScoreHandler handler) {
    g_scoreHandler = handler;
}

// Called from Unity (NativeAPI.native_sendScore).
void native_sendScore(int score) {
    if (g_scoreHandler != NULL) {
        g_scoreHandler(score);
    }
}

// Called from Unity (NativeAPI.native_sendMessage). We broadcast via NotificationCenter
// so any SwiftUI view can observe it.
void native_sendMessage(const char* message) {
    NSString *msg = message != NULL ? [NSString stringWithUTF8String:message] : @"";
    [[NSNotificationCenter defaultCenter] postNotificationName:@"UnityMessage"
                                                        object:nil
                                                      userInfo:@{@"message": msg}];
}

#ifdef __cplusplus
}
#endif
