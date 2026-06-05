import SwiftUI

// The capstone: Unity on top, a SwiftUI control panel below that sends commands into
// Unity and displays values Unity sends back.
struct CapstoneUnityView: View {
    @State private var events = UnityEvents()      // observes Unity -> native callbacks
    @State private var cubeColor = Color.red

    var body: some View {
        VStack(spacing: 0) {
            // --- Unity render area ---
            UnityContainerView()
                .frame(maxWidth: .infinity, maxHeight: .infinity)
                .ignoresSafeArea(edges: .top)

            // --- SwiftUI control panel ---
            VStack(spacing: 12) {
                HStack {
                    Label("\(events.score)", systemImage: "star.fill")
                        .font(.headline)
                    Spacer()
                    Text(events.lastMessage)
                        .font(.footnote)
                        .foregroundStyle(.secondary)
                }

                // SwiftUI -> Unity: push the chosen color to the cube.
                ColorPicker("Cube color", selection: $cubeColor)
                    .onChange(of: cubeColor) { _, newColor in
                        UnityBridge.shared.send(toObject: "SceneBridge",
                                                method: "SetColor",
                                                message: Self.rgbString(newColor))
                    }

                HStack {
                    Button("Spawn") {
                        UnityBridge.shared.send(toObject: "SceneBridge",
                                                method: "Spawn", message: "")
                    }
                    .buttonStyle(.borderedProminent)

                    Button("Unload Unity") {
                        UnityBridge.shared.unload()
                    }
                    .buttonStyle(.bordered)
                }
            }
            .padding()
            .background(.ultraThinMaterial)
        }
    }

    // Convert a SwiftUI Color into Unity's "r,g,b" (0..1) message format.
    private static func rgbString(_ color: Color) -> String {
        let ui = UIColor(color)
        var r: CGFloat = 0, g: CGFloat = 0, b: CGFloat = 0, a: CGFloat = 0
        ui.getRed(&r, green: &g, blue: &b, alpha: &a)
        return "\(Float(r)),\(Float(g)),\(Float(b))"
    }
}
