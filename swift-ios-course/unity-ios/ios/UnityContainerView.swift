import SwiftUI
import UIKit

// Hosts Unity's view inside SwiftUI by adding Unity's rootView to a hosted view
// controller (the Module 08 UIViewControllerRepresentable pattern applied to Unity).
struct UnityContainerView: UIViewControllerRepresentable {
    func makeUIViewController(context: Context) -> UIViewController {
        UnityBridge.shared.show()                       // launch / show Unity

        let container = UIViewController()
        if let unityView = UnityBridge.shared.rootView {
            unityView.translatesAutoresizingMaskIntoConstraints = false
            container.view.addSubview(unityView)
            NSLayoutConstraint.activate([
                unityView.topAnchor.constraint(equalTo: container.view.topAnchor),
                unityView.bottomAnchor.constraint(equalTo: container.view.bottomAnchor),
                unityView.leadingAnchor.constraint(equalTo: container.view.leadingAnchor),
                unityView.trailingAnchor.constraint(equalTo: container.view.trailingAnchor),
            ])
        }
        return container
    }

    func updateUIViewController(_ uiViewController: UIViewController, context: Context) {}
}

// Observes Unity -> native callbacks (score via the registered handler, messages via
// NotificationCenter) and republishes them to SwiftUI.
@Observable
final class UnityEvents {
    var lastMessage = ""
    var score = 0

    init() {
        // String messages broadcast by native_sendMessage in NativeCallsPlugin.mm
        NotificationCenter.default.addObserver(forName: Notification.Name("UnityMessage"),
                                               object: nil, queue: .main) { [weak self] note in
            self?.lastMessage = note.userInfo?["message"] as? String ?? ""
        }
        // Score updates: install the C callback (a non-capturing @convention(c) closure).
        installScoreHandler()
        NotificationCenter.default.addObserver(forName: Notification.Name("UnityScore"),
                                               object: nil, queue: .main) { [weak self] note in
            self?.score = note.userInfo?["score"] as? Int ?? 0
        }
    }

    private func installScoreHandler() {
        // @convention(c) closures can't capture state, so we bounce through NotificationCenter.
        RegisterScoreHandler { score in
            NotificationCenter.default.post(name: Notification.Name("UnityScore"),
                                            object: nil, userInfo: ["score": Int(score)])
        }
    }
}
