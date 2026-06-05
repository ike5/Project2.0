import Foundation
import UIKit
import UnityFramework   // available after you embed UnityFramework.framework

// Controls the embedded Unity runtime. Singleton because Unity can only be loaded once
// per process. This follows Unity's UaaL pattern (version-sensitive — see unity-ios/README).
final class UnityBridge: NSObject, UnityFrameworkListener {
    static let shared = UnityBridge()

    private var ufw: UnityFramework?
    private(set) var isLoaded = false

    private func loadFrameworkIfNeeded() -> UnityFramework {
        if let ufw { return ufw }

        // Load the embedded framework bundle, then grab Unity's singleton.
        let path = Bundle.main.bundlePath + "/Frameworks/UnityFramework.framework"
        if let bundle = Bundle(path: path), !bundle.isLoaded { bundle.load() }

        let fw = UnityFramework.getInstance()!
        // Unity needs the host app's Mach-O header. Unity's sample sets this in Obj-C:
        //   [ufw setExecuteHeader:&_mh_execute_header];
        // Add a tiny Obj-C shim that calls setExecuteHeader, or copy it from Unity's
        // uaal-example. (Pure-Swift access to _mh_execute_header is awkward.)
        ufw = fw
        return fw
    }

    /// Launch Unity (first call) or re-show its window (subsequent calls).
    func show() {
        let fw = loadFrameworkIfNeeded()
        fw.setDataBundleId("com.unity3d.framework")
        fw.register(self)
        if isLoaded {
            fw.showUnityWindow()
        } else {
            fw.runEmbedded(withArgc: CommandLine.argc,
                           argv: CommandLine.unsafeArgv,
                           appLaunchOpts: nil)
            isLoaded = true
        }
    }

    func pause(_ paused: Bool) { ufw?.pause(paused) }

    func unload() { ufw?.unloadApplication() }   // triggers unityDidUnload below

    /// SwiftUI -> Unity: invoke `method(message)` on the GameObject named `object`.
    func send(toObject object: String, method: String, message: String) {
        ufw?.sendMessageToGO(withName: object, functionName: method, message: message)
    }

    /// Unity's root view — host it inside SwiftUI via a representable.
    var rootView: UIView? { ufw?.appController()?.rootView }

    // MARK: UnityFrameworkListener
    func unityDidUnload(_ notification: Notification!) {
        ufw?.unregisterFrameworkListener(self)
        ufw = nil
        isLoaded = false
    }
}
