# Challenge 08 — Reference Solution

### 1. WebView with a navigation-delegate Coordinator
```swift
struct WebView: UIViewRepresentable {
    let url: URL
    @Binding var isLoading: Bool

    func makeCoordinator() -> Coordinator { Coordinator(isLoading: $isLoading) }

    func makeUIView(context: Context) -> WKWebView {
        let webView = WKWebView()
        webView.navigationDelegate = context.coordinator     // UIKit delegate -> SwiftUI
        return webView
    }
    func updateUIView(_ webView: WKWebView, context: Context) {
        webView.load(URLRequest(url: url))
    }

    final class Coordinator: NSObject, WKNavigationDelegate {
        private let isLoading: Binding<Bool>
        init(isLoading: Binding<Bool>) { self.isLoading = isLoading }
        func webView(_ w: WKWebView, didStartProvisionalNavigation n: WKNavigation!) { isLoading.wrappedValue = true }
        func webView(_ w: WKWebView, didFinish n: WKNavigation!) { isLoading.wrappedValue = false }
        func webView(_ w: WKWebView, didFail n: WKNavigation!, withError e: Error) { isLoading.wrappedValue = false }
    }
}
// usage: overlay a ProgressView when isLoading.
```

### 2. Wrap a UISlider (two-way)
```swift
struct UIKitSlider: UIViewRepresentable {
    @Binding var value: Double

    func makeCoordinator() -> Coordinator { Coordinator(value: $value) }
    func makeUIView(context: Context) -> UISlider {
        let slider = UISlider()
        slider.addTarget(context.coordinator,
                         action: #selector(Coordinator.changed(_:)),
                         for: .valueChanged)               // target-action
        return slider
    }
    func updateUIView(_ slider: UISlider, context: Context) {
        slider.value = Float(value)                        // SwiftUI -> UIKit
    }
    final class Coordinator: NSObject {
        private let value: Binding<Double>
        init(value: Binding<Double>) { self.value = value }
        @objc func changed(_ sender: UISlider) { value.wrappedValue = Double(sender.value) }  // UIKit -> SwiftUI
    }
}
```
> SwiftUI's native `Slider` is far less code — bridge only when a control is UIKit-only.

### 3. Host SwiftUI in UIKit (child VC)
```swift
final class HostingDemoVC: UIViewController {
    private var message = "Hello" { didSet { rebuildHosted() } }
    private var hosting: UIHostingController<AnyView>?

    override func viewDidLoad() {
        super.viewDidLoad()
        rebuildHosted()
        let button = UIButton(type: .system, primaryAction: UIAction(title: "Change") { [weak self] _ in
            self?.message = "Updated from UIKit"
        })
        // ...lay out button...
    }
    private func rebuildHosted() {
        hosting?.willMove(toParent: nil); hosting?.view.removeFromSuperview(); hosting?.removeFromParent()
        let host = UIHostingController(rootView: AnyView(Text(message).font(.title)))
        addChild(host); view.addSubview(host.view); host.didMove(toParent: self)
        // ...constraints...
        hosting = host
    }
}
```

### 4. Mapping to Unity
- **`makeUIViewController`** → create/obtain Unity's root view controller (from
  `UnityFramework`) once and hand it to SwiftUI to display.
- **`updateUIViewController`** → push SwiftUI state into Unity (e.g. call
  `sendMessage` when a bound value changes) — the "SwiftUI → Unity" direction.
- **Coordinator** → the object Unity calls back into (via the native plugin /
  `NativeCallsProtocol`); it writes results into SwiftUI bindings — the "Unity → SwiftUI"
  direction.
