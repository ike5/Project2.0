# Challenge 08 — Interop Mastery

Notes/solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Web view with delegate.** Extend `WebView` to report loading state (`isLoading`)
   back to SwiftUI by making the Coordinator a `WKNavigationDelegate`
   (`didStartProvisionalNavigation` / `didFinish`). Show a SwiftUI `ProgressView` while loading.

2. **Wrap a UIKit control.** Bridge a `UISlider` (or `UITextView`) via
   `UIViewRepresentable` with a two-way `@Binding<Double>` (Coordinator as the
   target-action handler). Compare it to SwiftUI's native `Slider`.

3. **Hosting both ways.** Build a UIKit `UIViewController` (in code) that embeds a SwiftUI
   view via `UIHostingController` as a child VC, and have a button in UIKit update the
   hosted SwiftUI content.

4. **Map the pattern to Unity (short answer).** In one or two sentences each, describe how
   `makeUIViewController`, `updateUIViewController`, and the Coordinator will each
   correspond to embedding/controlling Unity in Module 09–10.

## Success criteria
- [ ] `WebView` reports loading via a `WKNavigationDelegate` Coordinator.
- [ ] A UIKit control bridged with a working two-way binding.
- [ ] SwiftUI hosted inside a UIKit VC, updatable from UIKit.
- [ ] Clear mapping of the representable lifecycle to Unity embedding.
