import SwiftUI
import UIKit

// The simplest possible UIViewRepresentable: a UIKit spinner driven by SwiftUI state.
struct ActivityIndicator: UIViewRepresentable {
    var isAnimating: Bool

    func makeUIView(context: Context) -> UIActivityIndicatorView {
        let view = UIActivityIndicatorView(style: .large)
        view.hidesWhenStopped = true
        return view
    }

    func updateUIView(_ uiView: UIActivityIndicatorView, context: Context) {
        if isAnimating { uiView.startAnimating() } else { uiView.stopAnimating() }
    }
}
