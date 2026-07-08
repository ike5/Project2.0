# Lab 12 — I/O & NIO.2 Hands-On

**You'll:** read a small log file, parse it, and group entries by level.
⏱️ ~40 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop12 && cd ~/dev/oop12
mkdir -p src/com/example/files
mkdir -p data
```

## Part B — A log file

`data/sample.log`:
```
INFO  app started
WARN  deprecated method called
ERROR something bad happened
INFO  request handled
DEBUG retrying
ERROR another bad thing
```

## Part C — A small parser

`src/com/example/files/Entry.java`:
```java
package com.example.files;

public record Entry(String level, String message) {}
```

`src/com/example/files/LogIndex.java`:
```java
package com.example.files;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.List;
import java.util.Map;
import java.util.Objects;
import java.util.stream.Collectors;

public final class LogIndex {
    private LogIndex() {}

    public static List<Entry> parse(Path log) throws IOException {
        try (var lines = Files.lines(log)) {
            return lines
                .filter(s -> !s.isBlank())
                .map(LogIndex::parseLine)
                .filter(Objects::nonNull)
                .toList();
        }
    }

    public static Entry parseLine(String line) {
        int sp = line.indexOf(' ');
        if (sp <= 0) return null;
        return new Entry(line.substring(0, sp), line.substring(sp + 1).trim());
    }

    public static Map<String, Long> countByLevel(List<Entry> entries) {
        return entries.stream().collect(Collectors.groupingBy(
                Entry::level, Collectors.counting()));
    }
}
```

## Part D — Driver

`src/com/example/files/Main.java`:
```java
package com.example.files;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;

public class Main {
    public static void main(String[] args) throws IOException {
        // Write a sample log so the lab is self-contained.
        Path log = Path.of("data/sample.log");
        Files.createDirectories(log.getParent());
        Files.writeString(log, """
                INFO  app started
                WARN  deprecated method called
                ERROR something bad happened
                INFO  request handled
                DEBUG retrying
                ERROR another bad thing
                """);

        var entries = LogIndex.parse(log);
        System.out.println("entries: " + entries);
        System.out.println("counts: " + LogIndex.countByLevel(entries));
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.files.Main
```

Expected:
```
entries: [Entry[level=INFO, message=app started], Entry[level=WARN, ...], ...]
counts: {INFO=2, WARN=1, ERROR=2, DEBUG=1}
```

## Part E — Demonstrate `Files.walk`

Add a small block to `Main` that counts all `.java` files under a
directory (use `src` here):
```java
try (var walk = Files.walk(Path.of("src"))) {
    long javaCount = walk.filter(p -> p.toString().endsWith(".java")).count();
    System.out.println("java files: " + javaCount);
}
```

## Part F — Try `Serializable` (optional)

Add a `transient` field to a `record` and try to serialise it:
```java
record User(String name, transient int age) implements Serializable {
    @java.io.Serial private static final long serialVersionUID = 1L;
}
```
(Records can implement `Serializable` since Java 16.) The default
serialisation ignores `transient` fields. After deserialise, `age` will
be `0`.

## What you learned

- `Path` is the modern file representation; `Files` does the work.
- `Files.readString` / `writeString` for whole-file I/O.
- `Files.lines` for streaming a file line by line; combine with streams.
- `Files.walk` for recursive directory traversal.
- Always use `try`-with-resources; everything is `AutoCloseable`.
- `Serializable` works but has real pitfalls; prefer JSON for new code.

➡️ **[challenge.md](./challenge.md)** then [Module 13](../13-modules-jpms/).
