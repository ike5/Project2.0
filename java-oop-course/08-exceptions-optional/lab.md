# Lab 08 — Exceptions, `try`-with-resources & `Optional`

**You'll:** build an `IntParser` and a small `FileCopier` to exercise
checked exceptions, `try`-with-resources, and `Optional`. ⏱️ ~45 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop08 && cd ~/dev/oop08
mkdir -p src/com/example/parser
```

## Part B — `IntParser` with `Optional` and a throwing variant

`src/com/example/parser/IntParser.java`:
```java
package com.example.parser;

import java.util.OptionalInt;

public final class IntParser {
    private IntParser() {}

    public static OptionalInt tryParse(String s) {
        if (s == null) return OptionalInt.empty();
        try {
            return OptionalInt.of(Integer.parseInt(s.trim()));
        } catch (NumberFormatException e) {
            return OptionalInt.empty();
        }
    }

    public static int parseOrThrow(String s) {
        return tryParse(s).orElseThrow(() ->
                new IllegalArgumentException("not an int: " + s));
    }
}
```

## Part C — A `FileCopier` with `try`-with-resources

`src/com/example/parser/FileCopier.java`:
```java
package com.example.parser;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;

public final class FileCopier {
    private FileCopier() {}

    public static long copy(Path source, Path target) throws IOException {
        try (InputStream  in  = Files.newInputStream(source);
             OutputStream out = Files.newOutputStream(target)) {
            return in.transferTo(out);
        }
    }
}
```

## Part D — Driver

`src/com/example/parser/Main.java`:
```java
package com.example.parser;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.OptionalInt;

public class Main {
    public static void main(String[] args) throws IOException {
        // 1. parse, with Optional and throw variants.
        for (String s : new String[]{"42", "  7  ", "oops", null}) {
            OptionalInt v = IntParser.tryParse(s);
            System.out.println("tryParse(\"" + s + "\") = " +
                    (v.isPresent() ? v.getAsInt() : "<empty>"));
        }
        try { IntParser.parseOrThrow("not a number"); }
        catch (IllegalArgumentException e) { System.out.println("rejected: " + e.getMessage()); }

        // 2. copy with try-with-resources.
        Path src = Path.of("/tmp/oop08-src.txt");
        Path dst = Path.of("/tmp/oop08-dst.txt");
        Files.writeString(src, "Hello, exceptions!");
        long n = FileCopier.copy(src, dst);
        System.out.println("copied " + n + " bytes; dst says: " + Files.readString(dst));
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.parser.Main
```

Expected:
```
tryParse("42") = 42
tryParse("  7  ") = 7
tryParse("oops") = <empty>
tryParse("null") = <empty>
rejected: not a number: not a number
copied 19 bytes; dst says: Hello, exceptions!
```

## Part E — A custom exception

Add a checked exception and a service that throws it on missing input:

`src/com/example/parser/ServiceException.java`:
```java
package com.example.parser;

public final class ServiceException extends Exception {
    private static final long serialVersionUID = 1L;
    public ServiceException(String message)                  { super(message); }
    public ServiceException(String message, Throwable cause) { super(message, cause); }
}
```

`src/com/example/parser/ConfigService.java`:
```java
package com.example.parser;

import java.util.Optional;
import java.util.Properties;

public final class ConfigService {
    private final Properties props;
    public ConfigService(Properties props) { this.props = props; }

    public Optional<String> get(String key) {
        return Optional.ofNullable(props.getProperty(key));
    }

    public int requireInt(String key) throws ServiceException {
        String raw = get(key).orElseThrow(() -> new ServiceException("missing key: " + key));
        return IntParser.tryParse(raw).orElseThrow(() ->
                new ServiceException("not an int at " + key + ": " + raw));
    }
}
```

Update `Main` to use it:
```java
var props = new Properties();
props.setProperty("port", "8080");
var cfg = new ConfigService(props);
try { System.out.println("port: " + cfg.requireInt("port")); }
catch (ServiceException e) { System.out.println("rejected: " + e.getMessage()); }
try { System.out.println("host: " + cfg.requireInt("host")); }    // missing
catch (ServiceException e) { System.out.println("rejected: " + e.getMessage()); }
```

## Part F — `OptionalInt` vs. `Optional<Integer>`

A small note: `OptionalInt` holds a primitive `int` with no boxing.
`Optional<Integer>` boxes the int into an `Integer`. Use `OptionalInt`
when the value is genuinely a primitive. For reference types, use
`Optional<T>`.

## What you learned

- `try`-with-resources auto-closes everything `AutoCloseable` and
  handles suppressed exceptions for you.
- Checked exceptions are for *recoverable external* conditions; unchecked
  for *precondition violations*. Choose deliberately.
- Custom exceptions are easy: extend `Exception` (checked) or
  `RuntimeException` (unchecked), provide `(String)` and `(String,
  Throwable)` constructors.
- `Optional` is for return types where the empty case is expected; never
  for fields or parameters.

➡️ **[challenge.md](./challenge.md)** then [Module 09](../09-enums-nested/).
