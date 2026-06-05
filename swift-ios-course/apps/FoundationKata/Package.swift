// swift-tools-version: 5.9
import PackageDescription

// A pure-Swift/Foundation package — no Apple-UI frameworks — so it builds and tests
// with `swift build` / `swift test` on macOS (and the cross-platform subset on Linux).
let package = Package(
    name: "FoundationKata",
    products: [
        .library(name: "FoundationKata", targets: ["FoundationKata"]),
    ],
    targets: [
        .target(name: "FoundationKata"),
        .testTarget(name: "FoundationKataTests", dependencies: ["FoundationKata"]),
    ]
)
