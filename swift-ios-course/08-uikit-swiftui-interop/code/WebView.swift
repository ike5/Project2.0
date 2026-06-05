import SwiftUI
import WebKit

// Wrap a UIKit/WebKit WKWebView so SwiftUI can show it. makeUIView creates the view once;
// updateUIView pushes SwiftUI state (the URL) into it.
struct WebView: UIViewRepresentable {
    let url: URL

    func makeUIView(context: Context) -> WKWebView {
        WKWebView()
    }

    func updateUIView(_ webView: WKWebView, context: Context) {
        webView.load(URLRequest(url: url))
    }
}
