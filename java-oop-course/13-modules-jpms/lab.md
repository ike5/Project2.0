# Lab 13 — Two Modules and a Custom JRE

**You'll:** build a `greeter` library module and an `app` module that
uses it. Package both as modular JARs, then `jlink` a custom JRE. ⏱️ ~40 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop13 && cd ~/dev/oop13
mkdir -p greeter/src/com/example/greeter
mkdir -p app/src/com/example/app
mkdir -p mods
```

## Part B — `greeter` module

`greeter/src/module-info.java`:
```java
module com.example.greeter {
    exports com.example.greeter;
}
```

`greeter/src/com/example/greeter/Greeter.java`:
```java
package com.example.greeter;

public final class Greeter {
    public static String greet(String name) { return "Hello, " + name; }
    private Greeter() {}
}
```

Compile + package:
```bash
javac -d greeter/out greeter/src/module-info.java greeter/src/com/example/greeter/Greeter.java
jar --create --file=mods/greeter.jar --module-version=1.0 -C greeter/out .
```

## Part C — `app` module

`app/src/module-info.java`:
```java
module com.example.app {
    requires com.example.greeter;
}
```

`app/src/com/example/app/Main.java`:
```java
package com.example.app;

import com.example.greeter.Greeter;

public class Main {
    public static void main(String[] args) {
        System.out.println(Greeter.greet("modular Java"));
    }
}
```

Compile + package:
```bash
javac -d app/out --module-path mods app/src/module-info.java app/src/com/example/app/Main.java
jar --create --file=mods/app.jar --module-version=1.0 --main-class=com.example.app.Main -C app/out .
```

## Part D — Run

```bash
java --module-path mods --module com.example.app
```

Expected: `Hello, modular Java`.

## Part E — `jlink` a custom JRE

```bash
jlink \
    --module-path "$JAVA_HOME/jmods:mods" \
    --add-modules com.example.app \
    --output custom-jre \
    --strip-debug --compress=zip-9
ls custom-jre/bin/
./custom-jre/bin/java --module-path mods --module com.example.app
```

The `custom-jre` directory now contains a complete, runnable JRE
containing only the modules your app needs — typically ~40-60 MB instead
of the full ~150 MB. You can copy this directory to any machine and run
your app without an installed JDK.

## Part F — Try `jpackage` (optional, requires GUI toolchain)

```bash
jpackage \
    --name HelloApp \
    --module-path mods \
    --add-modules com.example.app \
    --main-class com.example.app.Main \
    --type app-image \
    --dest dist
ls dist/HelloApp/
dist/HelloApp/bin/HelloApp     # a launcher script
```

This produces a folder with a launcher; `jpackage --type dmg` (macOS) or
`--type msi` (Windows) wraps it in a real installer.

## What you learned

- A module is a JAR with a `module-info.class` that declares its
  dependencies and exports.
- `requires` makes a module visible to your module; `exports` makes a
  package visible to other modules.
- `jlink` builds a custom JRE containing only the modules you need.
- `jpackage` produces a real installer for end users.

➡️ **[challenge.md](./challenge.md)** then [Module 14](../14-design-patterns/).
