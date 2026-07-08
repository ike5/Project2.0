# Module 13 — Modules (JPMS) & Packaging

**Goal:** understand Java's module system at a working level. Write a
`module-info.java`, declare `requires` and `exports`, and use `jlink` to
build a custom JRE for your application.

⏱️ ~1.5 h · 🎯 Prereq: Module 12.

---

## 1. The classpath's problem

Before modules (Java 8 and earlier), the classpath was a long list of
JARs and directories. There was no enforcement of:

- Which packages a JAR exposes.
- Whether two JARs on the classpath contain the *same* class file
  (split packages).
- Whether a JAR's missing dependencies would be caught at compile time
  or only at runtime (usually "deep in production").

JPMS — the **Java Platform Module System** — fixes this. A module is a
JAR with a `module-info.class` (compiled from `module-info.java`) that
declares its **dependencies** and the **packages it exports**.

## 2. The shape of a module

```
my-app/
├── module-info.java
└── com/example/app/
    └── Main.java
```

`module-info.java`:
```java
module com.example.app {
    requires com.example.greeter;     // depend on another module
    exports com.example.app;          // expose a package
}
```

`Main.java`:
```java
package com.example.app;
import com.example.greeter.Greeter;
public class Main {
    public static void main(String[] args) {
        System.out.println(Greeter.greet("modules"));
    }
}
```

A few rules:
- Module name and package names are **independent**. Convention: use the
  reverse-DNS name of the project.
- A module is *one* JAR. (Multi-release JARs let you ship different
  bytecode for different Java versions, but it's one module.)
- A module is either named (in a JAR) or **automatic** (the unnamed
  module on the classpath — the bridge from old to new).

## 3. `module-info.java` directives

### `module`
Declares the module's name:
```java
module com.example.app { }
```

### `requires`
Declares a dependency on another module:
```java
requires java.logging;                  // a JDK module
requires com.example.greeter;            // your module
requires transitive com.example.greeter; // also re-exported
requires static com.fasterxml.jackson.core; // compile-time only
```

`transitive` means "if you `requires` me, you also `requires` the things
I require." Use it for API dependencies that show up in your public
types.

### `exports`
Makes a package visible to other modules:
```java
exports com.example.api;
exports com.example.spi to com.example.impl;  // qualified export
```

The unqualified `exports` is the default. **Qualified exports** are for
SPI packages that only a few consumers should see.

### `opens`
Allows **reflection** access to a package at runtime. Required for
frameworks like Jackson, Hibernate, JPA:
```java
opens com.example.model to com.fasterxml.jackson.databind;
```

### `provides ... with`
Declares a service provider:
```java
provides com.example.spi.PaymentProcessor with com.example.impl.StripeProcessor;
```

### `uses`
Declares that this module consumes a service:
```java
uses com.example.spi.PaymentProcessor;
```

### `open module`
An "open module" is one that exports all packages for reflection. Use
sparingly — it defeats the purpose of encapsulation.

## 4. Module-path vs. classpath

- **`--module-path` (or `-p`)** — list of modular JARs (or directories
  containing them).
- **`--class-path` (or `-cp`)** — the old style, for libraries that
  aren't modular.

A modular JAR on the classpath becomes an **automatic module**: its
name is derived from the JAR's filename, and it exports all packages
(but the encapsulation rules still apply to the explicit modules that
*require* it).

You can mix: put your application modules on `--module-path` and old
dependencies on `--class-path`.

## 5. The unnamed module

Code on the classpath lives in the **unnamed module**. It can read any
exported package, but it can't `require` anything. This is the bridge
that lets you adopt modules gradually.

## 6. Compiling and running a modular app

```bash
# Layout
# greeter/src/module-info.java
# greeter/src/com/example/greeter/Greeter.java
# app/src/module-info.java
# app/src/com/example/app/Main.java

# Compile each
javac -d greeter/out greeter/src/module-info.java greeter/src/com/example/greeter/Greeter.java
javac -d app/out --module-path greeter/out app/src/module-info.java app/src/com/example/app/Main.java

# Package each
jar --create --file=greeter.jar --module-version=1.0 -C greeter/out .
jar --create --file=app.jar     --module-version=1.0 --main-class=com.example.app.Main -C app/out .

# Run
java --module-path greeter.jar:app.jar --module com.example.app/com.example.app.Main
```

The `--main-class` flag in the JAR's manifest makes the JAR runnable:
```bash
java --module-path greeter.jar:app.jar -m com.example.app
```

## 7. `jlink` — build a custom JRE

A "JRE" is the JVM plus the standard library. `jlink` builds a *minimal*
JRE that contains only the modules your app needs.

```bash
jlink \
  --module-path "$JAVA_HOME/jmods:mods" \
  --add-modules com.example.app \
  --output custom-jre \
  --strip-debug --compress=zip-9
```

The output is a directory with `bin/java`. You can run your app on a
target machine that has *no JDK installed*:

```bash
./custom-jre/bin/java --module custom-jre/mods/com.example.app.jar -m com.example.app
```

For a real desktop installer, `jpackage` (next section) wraps this with
the rest of the application.

## 8. `jpackage` — native installer

```bash
jpackage \
  --name MyApp \
  --input lib/ \
  --main-jar app.jar \
  --main-class com.example.app.Main \
  --type dmg
```

Produces a `.dmg` (macOS), `.msi` (Windows), or `.deb` (Linux) that
installs the JDK, your JAR, and a launcher — a single file the user
double-clicks.

## 9. Common mistakes

- **Forgetting `module-info.java`** → your code is in the unnamed
  module and can't be `required` by anyone.
- **Exporting implementation packages** → defeats encapsulation. Make
  your packages `package-private` (no `public`) by default; only
  `public class`es in `exports`ed packages are reachable.
- **Forgetting to `opens` for reflection** → `Jackson` (and similar)
  fails to deserialise at runtime. Use `opens com.example.model to
  jackson.databind;`.
- **Two modules exporting the same package** → `package x is in both
  module a and module b`. JPMS forbids this. Reorganise.
- **The `--module-path` is not a "list of all JARs"** — it's a list of
  *modules*. JARs on the classpath are the bridge, not a replacement.

## 10. When to use modules

- **Yes** for any library you're publishing or shipping — the
  encapsulation is worth the ceremony.
- **Yes** for any application with a clean module graph.
- **Maybe later** for legacy codebases — modules work alongside the
  classpath; you can adopt gradually.

For a single small program, you can stay on the classpath forever. For
anything you intend to grow, prefer modules.

## 11. Module naming convention

Use reverse-DNS to match package names:
- `com.example.greeter` for the package `com.example.greeter`.
- `com.example.greeter` for the module too.

Or use a project-specific prefix: `io.grpc.netty`, `org.apache.commons.lang3`.
The module name is the public name of your library; pick carefully.

---

## Do the lab

Build a two-module app: a `greeter` library and an `app` that uses it,
then `jlink` a custom JRE. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

module · `module-info.java` · `requires` / `requires transitive` /
`requires static` · `exports` / `exports to` · `opens` / `opens to` ·
`provides ... with` / `uses` · automatic module · unnamed module ·
`--module-path` (`-p`) · `--class-path` (`-cp`) · `--module` (`-m`) ·
`jlink` · custom JRE · `jpackage` · `jmod`

**Next →** [Module 14: Design Patterns in Modern Java](../14-design-patterns/)
