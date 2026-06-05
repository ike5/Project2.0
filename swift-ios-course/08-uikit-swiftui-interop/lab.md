# Lab 08 — Bridge UIKit into SwiftUI

**You'll:** host UIKit views and a view controller in SwiftUI, with a Coordinator passing
data both ways. ⏱️ ~55 min. Add the three files from `code/` to a project (PlacesApp or a
scratch app).

---

## Part A — A wrapped web view
Add `WebView.swift`. Use it:
```swift
struct WebScreen: View {
    var body: some View {
        WebView(url: URL(string: "https://developer.apple.com")!)
            .ignoresSafeArea()
    }
}
```
Run. ✅ A real `WKWebView` (UIKit/WebKit) renders inside SwiftUI. Note: `makeUIView`
created it; `updateUIView` loaded the URL.

## Part B — A wrapped spinner driven by state
Add `ActivityIndicator.swift`. Drive it from SwiftUI state:
```swift
struct SpinnerDemo: View {
    @State private var busy = false
    var body: some View {
        VStack(spacing: 20) {
            ActivityIndicator(isAnimating: busy)
            Button(busy ? "Stop" : "Start") { busy.toggle() }
        }
    }
}
```
Run → toggling `busy` starts/stops the UIKit spinner. ✅ SwiftUI state → UIKit via
`updateUIView`.

## Part C — A view controller with two-way data (the key pattern)
Add `CounterView.swift`. Embed it and observe both directions:
```swift
struct InteropDemo: View {
    @State private var count = 0
    var body: some View {
        VStack(spacing: 16) {
            Text("SwiftUI sees: \(count)").font(.title2)

            CounterView(count: $count)                 // the embedded UIKit VC
                .frame(height: 180)
                .clipShape(RoundedRectangle(cornerRadius: 12))

            Button("Increment (SwiftUI)") { count += 1 }   // SwiftUI -> UIKit
        }
        .padding()
    }
}
```
Run and test **both** directions:
- Tap **Increment (UIKit)** inside the embedded controller → the UIKit `didSet` fires
  `onCountChanged` → the **Coordinator** writes the binding → "SwiftUI sees:" updates.
- Tap **Increment (SwiftUI)** → `count` changes → `updateUIViewController` calls
  `setCount` → the UIKit label updates.

✅ You have a **two-way bridge** between SwiftUI and UIKit through a Coordinator. The
UIKit side used **target-action** and a closure callback — pure Objective-C heritage.

## Part D — SwiftUI inside UIKit (the reverse)
In a scratch UIKit context (or just read this), SwiftUI hosts via `UIHostingController`:
```swift
let host = UIHostingController(rootView: Text("SwiftUI on top of UIKit"))
someUIViewController.present(host, animated: true)
```
> In Module 09 you'll embed Unity's **UIViewController** with these same
> representable/Coordinator techniques, and overlay SwiftUI controls using
> `UIHostingController`.

## Part E — Connect the dots to Unity
Re-read the two-way flow in Part C. When we embed Unity:
- **SwiftUI → Unity** ≈ `updateUIViewController`/explicit calls → `sendMessage` to a Unity GameObject.
- **Unity → SwiftUI** ≈ UIKit callback → Coordinator → binding (Unity calls a native
  function that updates SwiftUI state).

Same shape, different engine.

## What you learned
- `UIViewRepresentable` / `UIViewControllerRepresentable` to host UIKit in SwiftUI.
- The **Coordinator** as the delegate/callback bridge (UIKit → SwiftUI).
- Pushing SwiftUI state into UIKit via `update...`.
- `UIHostingController` to host SwiftUI in UIKit — and how this all maps to Unity.

➡️ **[challenge.md](./challenge.md)** then [Module 09](../09-embedding-unity-uaal/).
