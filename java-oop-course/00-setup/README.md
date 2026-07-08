# Module 00 — Setup & Orientation

**Goal:** install a Java 21 toolchain and an editor, then build and run your
first Java program. ⏱️ ~45 min.

---

## What you're installing

| Tool | What it is | Why |
|------|-----------|-----|
| **JDK 21 (LTS)** | Compiler (`javac`), JRE (`java`), libraries, `jar`, `jlink` | Build and run everything in this course |
| **VS Code** + **Extension Pack for Java** | Lightweight editor with Java support & debugger | Default editor (free) |
| **IntelliJ IDEA Community** *(optional)* | Full Java IDE | Excellent if you prefer a heavier IDE (free) |

> You only need **one** editor. We give VS Code steps; IntelliJ works
> identically for the labs (its debugger and test runner are first-class).

## Step 1 — Install the JDK 21

**Option A (Homebrew, recommended):**
```bash
brew install --cask temurin@21
```
This installs the [Eclipse Temurin](https://adoptium.net/) JDK 21, the most
common open-source distribution.

**Option B (manual):** download **JDK 21** for macOS (Arm64 for Apple
Silicon, x64 for Intel) from <https://adoptium.net/>.

Verify:
```bash
java --version      # 21.x.y
javac --version     # 21.x.y
jar --version       # 21.x.y
```

If `java` isn't found, open a new terminal (PATH refresh) or check the
Homebrew caveats.

## Step 2 — Set `JAVA_HOME`

Some tools (Gradle, Maven, IntelliJ, `jlink`) need `JAVA_HOME` set:

```bash
# Homebrew + Temurin:
export JAVA_HOME="$(/usr/libexec/java_home -v 21)"
# Add to ~/.zshrc to persist:
echo 'export JAVA_HOME="$(/usr/libexec/java_home -v 21)"' >> ~/.zshrc
```

Verify:
```bash
echo "$JAVA_HOME"           # /Library/Java/JavaVirtualMachines/temurin-21.jdk/Contents/Home
"$JAVA_HOME/bin/java" --version
```

## Step 3 — Install an editor

**VS Code:**
```bash
brew install --cask visual-studio-code
```
Then in VS Code, install the **Extension Pack for Java** (it pulls in
language support, debugger, test runner, Maven/Gradle integration). Open the
Extensions panel (`Cmd+Shift+X`), search "Extension Pack for Java", Install.

**IntelliJ IDEA Community (optional alternative):**
```bash
brew install --cask intellij-idea-ce
```

## Step 4 — Hello, Java

```bash
mkdir -p ~/dev/hello && cd ~/dev/hello
cat > Hello.java <<'EOF'
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello, Java " + Runtime.version());
    }
}
EOF

javac Hello.java      # produces Hello.class
java Hello            # runs the class
```

Expected: `Hello, Java 21.0.x` (or whatever your runtime version is).

Open the folder in your editor. Look at the two files:
- **`Hello.java`** — the source. The class is `public`, so the file must be
  named `Hello.java`. The method `public static void main(String[] args)` is
  the entry point.
- **`Hello.class`** — the bytecode. You usually don't edit or read this
  directly.

Try the modern single-file launch (Java 11+, no compile step):
```bash
java Hello.java       # compiles in memory and runs
```

## Step 5 — A package + a real layout

Java projects use *packages* (namespaces) that map to directory structure.

```bash
mkdir -p ~/dev/hello2/src/com/example && cd ~/dev/hello2
cat > src/com/example/Greeter.java <<'EOF'
package com.example;

public class Greeter {
    public static String greet(String name) {
        return "Hello, " + name;
    }
}
EOF

cat > src/com/example/Main.java <<'EOF'
package com.example;

public class Main {
    public static void main(String[] args) {
        System.out.println(Greeter.greet("Java"));
    }
}
EOF

javac -d out $(find src -name '*.java')
java -cp out com.example.Main
```

Expected: `Hello, Java`.

```
hello2/
├── src/
│   └── com/example/
│       ├── Greeter.java
│       └── Main.java
└── out/                        (created by javac)
    └── com/example/
        ├── Greeter.class
        └── Main.class
```

This is the same shape every Java project has. Later modules you'll use a
build tool (Gradle) to automate this.

## Step 6 — Verify

```bash
cd java-oop-course/00-setup
./scripts/verify-setup.sh
```

Then run the full [../VERIFY.md](../VERIFY.md) smoke test to confirm the
end-to-end workflow works.

---

## Editor tips

- **VS Code**: enable **Format on save** in settings; install **Java
  Language Support** if not pulled in by the extension pack.
- **IntelliJ**: use `Cmd+Shift+F10` to run, `Cmd+Shift+F9` to debug. The
  *Project* view should show packages, not files.
- **Run/Debug from the editor**: VS Code's Run/Debug view runs the current
  class; IntelliJ's gutter icons do the same.

## Troubleshooting

- **`java: command not found`** → new terminal, or check `echo $PATH | tr ':'
  '\n' | grep java`.
- **`java --version` shows 8 or 11** → your `PATH` is picking up an older
  Java. Set `JAVA_HOME` and prepend `$JAVA_HOME/bin` to `PATH`.
- **`javac: file not found`** → check the filename matches the public class
  *exactly* (case-sensitive), including the `.java` extension.
- **Editor complains about `JAVA_HOME`** → set it (see Step 2). The
  Extension Pack for Java uses it for its language server.
- **`mvn` or `gradle` not found** → not needed yet. We use `javac` and
  `java` directly in early modules. We add Gradle in Module 15.

---

**Next →** [Module 01: Java Fast-Track](./01-java-fast-track/)
