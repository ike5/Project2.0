// Bridging header — exposes the plugin's C functions to Swift.
// Set this as the target's "Objective-C Bridging Header" in Build Settings
// (SWIFT_OBJC_BRIDGING_HEADER). Xcode offers to create one automatically when you add
// the first Objective-C/.mm file to a Swift target.

#ifndef App_Bridging_Header_h
#define App_Bridging_Header_h

typedef void (*ScoreHandler)(int);

// Implemented in NativeCallsPlugin.mm:
void RegisterScoreHandler(ScoreHandler handler);
void native_sendScore(int score);
void native_sendMessage(const char* message);

#endif /* App_Bridging_Header_h */
