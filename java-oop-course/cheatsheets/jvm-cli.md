# JVM CLI Cheatsheet

The four commands you need to know: `javac`, `java`, `jar`, `jlink`. Plus
`jpackage` for shipping.

## `javac` — compile

```bash
javac Hello.java                              # single file
javac src/com/example/*.java -d out           # whole package, output to out/
javac --release 21 Foo.java                   # target Java 21 bytecode
javac -Xlint:all,serial -Werror Foo.java      # strict, treat warnings as errors
javac -cp 'libs/*' -d out $(find src -name '*.java')     # with classpath
```

Useful flags:
- `-d <dir>` — output directory for `.class` files.
- `-cp`/`-classpath` — where to find dependencies.
- `--release N` — compile for JVM N (the right way, not `-source/-target`).
- `-Xlint:all` — turn on all lint checks.
- `-parameters` — keep method parameter names at runtime (useful for
  reflection / JSON binding).

## `java` — run

```bash
java Hello                                   # class in current dir on classpath
java -cp out com.example.Hello                # class in package, output dir
java -jar app.jar                             # run a JAR
java -p mods:libs -m com.example.app/Main     # run a modular app
java --enable-preview --source 21 Foo.java    # preview features
```

Useful flags:
- `-cp`/`-classpath` — directories and JARs to search.
- `-p`/`--module-path` — directory or directory of modular JARs.
- `-m`/`--module` — module and class to run (`module/Main`).
- `-ea`/`-da` — enable/disable `assert` statements.
- `-Dname=value` — system property (`System.getProperty("name")`).
- `-Xmx2g -Xms256m` — max / initial heap size.
- `-XX:+UseG1GC` — choose a GC.

## `jar` — package

```bash
jar --create --file=app.jar -C out .          # create from compiled classes
jar --create --file=app.jar --main-class=com.example.Main -C out .   # runnable JAR
jar --list --file=app.jar                     # show contents
jar --extract --file=app.jar                  # unpack
jar --update --file=app.jar -C out .          # add files
```

A *runnable* JAR is one with `Main-Class:` in `META-INF/MANIFEST.MF`.

## `jlink` — custom JRE

Build a JRE containing only the modules your app needs:

```bash
jlink \
  --module-path "$JAVA_HOME/jmods" \
  --add-modules java.base,java.sql,java.logging \
  --output custom-jre \
  --strip-debug --compress=zip-9
```

The result is a directory with `bin/java` you can run on a target machine
that has *no JDK installed*.

## `jpackage` — native installer

```bash
jpackage \
  --name MyApp \
  --input libs/ \
  --main-jar app.jar \
  --main-class com.example.Main \
  --type dmg          # or msi / deb / rpm / pkg / app-image
```

`jpackage` runs `jlink` internally and bundles the custom JRE with your app
into a native installer.

## `jmod` — module JMOD files

JDK 9+ ships modules as `.jmod` files in `$JAVA_HOME/jmods`. Tools like
`jlink` read them. You don't usually need to touch `jmod` directly.

## Module compilation

```bash
# Compile a module
javac -d out/m src/module-info.java src/com/example/app/*.java

# Package as modular JAR
jar --create --file=mods/com.example.app.jar --module-version=1.0 -C out/m .

# Compile a downstream module that depends on it
javac -d out/c --module-path mods src/module-info.java src/com/example/client/*.java
```

## Quick reference: single-file programs

Since Java 11 you can run a single file without compiling:

```bash
java Hello.java Ada
```

Great for trying things. Not great for multi-file projects.

## Debugging & diagnosis

```bash
jps                  # list JVM processes and their PIDs
jstat -gc <pid> 1s   # GC stats every second
jstack <pid>         # thread dump
jmap -histo <pid>    # heap histogram (use with care; can pause)
jcmd <pid> help      # comprehensive diagnostics
```

These are *production* tools. Use them carefully — `jmap -dump` and similar
will pause the JVM.
