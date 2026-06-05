import SwiftUI
import UIKit

// A plain UIKit view controller that uses TARGET-ACTION (Objective-C heritage) and
// reports its count out via a closure. This stands in for any UIKit SDK — including
// Unity's view controller in Phase 2.
final class CounterViewController: UIViewController {
    var onCountChanged: ((Int) -> Void)?

    private var count = 0 {
        didSet {
            label.text = "UIKit count: \(count)"
            onCountChanged?(count)            // notify whoever embedded us
        }
    }
    private let label = UILabel()

    override func viewDidLoad() {
        super.viewDidLoad()
        view.backgroundColor = .secondarySystemBackground

        label.text = "UIKit count: 0"
        label.textAlignment = .center

        let button = UIButton(type: .system)
        button.setTitle("Increment (UIKit)", for: .normal)
        button.addTarget(self, action: #selector(increment), for: .touchUpInside)   // target-action

        let stack = UIStackView(arrangedSubviews: [label, button])
        stack.axis = .vertical
        stack.spacing = 12
        stack.translatesAutoresizingMaskIntoConstraints = false
        view.addSubview(stack)
        NSLayoutConstraint.activate([
            stack.centerXAnchor.constraint(equalTo: view.centerXAnchor),
            stack.centerYAnchor.constraint(equalTo: view.centerYAnchor),
        ])
    }

    // Lets SwiftUI push a value DOWN into UIKit.
    func setCount(_ newValue: Int) {
        if newValue != count { count = newValue }
    }

    @objc private func increment() { count += 1 }
}

// Bridge the controller into SwiftUI. The Coordinator forwards UIKit callbacks into a Binding.
struct CounterView: UIViewControllerRepresentable {
    @Binding var count: Int

    func makeCoordinator() -> Coordinator { Coordinator(count: $count) }

    func makeUIViewController(context: Context) -> CounterViewController {
        let vc = CounterViewController()
        vc.onCountChanged = context.coordinator.handleCountChanged   // UIKit -> SwiftUI
        return vc
    }

    func updateUIViewController(_ uiViewController: CounterViewController, context: Context) {
        uiViewController.setCount(count)                              // SwiftUI -> UIKit
    }

    final class Coordinator {
        private let count: Binding<Int>
        init(count: Binding<Int>) { self.count = count }
        func handleCountChanged(_ newValue: Int) { count.wrappedValue = newValue }
    }
}
