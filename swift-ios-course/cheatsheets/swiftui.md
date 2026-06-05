# SwiftUI Cheatsheet

Declarative UI on Apple platforms. A view is a **value type** describing UI; SwiftUI
re-renders it when state changes.

## A view
```swift
import SwiftUI

struct GreetingView: View {
    let name: String
    var body: some View {            // 'some View' = an opaque concrete View
        Text("Hello, \(name)!")
            .font(.title)            // modifiers return a new view
            .padding()
            .foregroundStyle(.blue)
    }
}
```

## Layout
```swift
VStack(spacing: 12) { ... }          // vertical
HStack { ... }                       // horizontal
ZStack { ... }                       // depth (overlap)
Spacer(); Divider()
LazyVStack / LazyHStack              // lazy (for long scrolls)
ScrollView { ... }
Grid { GridRow { ... } }
```
Common modifiers: `.padding()`, `.frame(width:height:)`, `.background()`,
`.foregroundStyle()`, `.font()`, `.cornerRadius()`, `.onTapGesture {}`, `.opacity()`.

## State management (the @-wrappers)
```swift
@State private var count = 0                 // local value-type state owned by this view
@Binding var isOn: Bool                       // two-way ref to state owned by a parent
@Observable class Model { var items = [] }    // observable reference type (iOS 17+)
@State private var model = Model()            // own an @Observable model
@Environment(\.colorScheme) var scheme        // read environment values
@AppStorage("username") var name = ""         // bound to UserDefaults
```
Pass bindings with `$`:
```swift
Toggle("On", isOn: $isOn)
TextField("Name", text: $name)
```

## Controls & collections
```swift
Button("Tap") { count += 1 }
TextField("Email", text: $email)
Toggle("Wi-Fi", isOn: $wifi)
Slider(value: $volume, in: 0...1)
Picker("Color", selection: $color) { Text("Red").tag("red") }

List(items) { item in Text(item.name) }       // items must be Identifiable
List { ForEach(items) { ... } .onDelete { ... } }
```

## Navigation
```swift
NavigationStack {
    List(items) { item in
        NavigationLink(item.name, value: item)
    }
    .navigationTitle("Items")
    .navigationDestination(for: Item.self) { item in DetailView(item: item) }
}
```
Sheets & alerts:
```swift
.sheet(isPresented: $showing) { EditView() }
.alert("Error", isPresented: $hasError) { Button("OK") {} }
```

## Lifecycle & async
```swift
.task { await load() }                 // runs async work when the view appears
.onAppear { } .onDisappear { }
.refreshable { await reload() }        // pull-to-refresh
```

## Previews (fast iteration)
```swift
#Preview {
    GreetingView(name: "Ada")
}
```
Previews render live in Xcode's canvas — your main feedback loop.

## Images & SF Symbols
```swift
Image(systemName: "map.fill")          // built-in SF Symbols icon
Image("myAsset")                       // from the asset catalog
.resizable().scaledToFit()
```

## Identifiable (needed for List/ForEach)
```swift
struct Item: Identifiable { let id = UUID(); var name: String }
```

> Mental model: **state drives the view**. You don't mutate views; you change state and
> SwiftUI recomputes `body`. Keep view structs small; put logic in `@Observable` models.
