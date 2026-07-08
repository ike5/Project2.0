# Module 08 — Exceptions, `try`-with-resources & `Optional`

**Goal:** design error handling that's *typed*, *recoverable*, and
*idiomatic*. Choose between checked and unchecked exceptions the right
way. Use `try`-with-resources for anything `AutoCloseable`. Use
`Optional<T>` for return types that may legitimately be empty.

⏱️ ~2 h · 🎯 Prereq: Module 07.

---

## 1. The three exception families

```
              Throwable
            /            \
         Error         Exception
       (don't catch)   /        \
                  RuntimeException   IOException, SQLException,
                  (unchecked)        ReflectiveOperationException, ...
                  NPE, IAE, ISE,     (CHECKED)
                  IndexOOB, ...
```

- **`Error`** — JVM problems you cannot recover from
  (`OutOfMemoryError`, `StackOverflowError`). Don't catch.
- **`RuntimeException`** — programming errors and precondition
  violations. Unchecked.
- **`Exception` (non-runtime)** — *external* conditions you should
  *anticipate and recover from* (`IOException`, `SQLException`,
  `ParseException`). **Checked**: the compiler forces you to either
  handle them with `try`/`catch` or declare them with `throws`.

## 2. Checked vs. unchecked — the rule

- **Use checked exceptions** for conditions the caller *can reasonably
  recover from* (file not found, network down, malformed input). Force
  the caller to think about it.
- **Use unchecked exceptions** for *precondition violations* and
  *programming errors* (`IllegalArgumentException`,
  `IllegalStateException`, `IndexOutOfBoundsException`).
- **Never use checked exceptions for control flow.** (i.e. don't catch
  and rethrow in a tight loop.)
- **Never throw `Exception` or `Throwable` directly.** Declare a
  meaningful subtype.

```java
public List<Order> readOrders(Path path) throws IOException {     // checked — caller decides
    try (var in = Files.newBufferedReader(path)) {
        return parse(in);
    }
}

public Order orderById(long id) {                                  // unchecked precondition
    if (id <= 0) throw new IllegalArgumentException("id must be > 0");
    /* ... */
}
```

## 3. The `try`/`catch`/`finally` form

```java
try {
    return compute(input);
} catch (IOException e) {
    log.warn("io failure", e);
    throw new ServiceException("compute failed", e);   // wrap & rethrow
} catch (NumberFormatException e) {                    // narrower types first
    throw new BadInputException("bad number", e);
} finally {
    cleanup();     // always runs (use try-with-resources instead when possible)
}
```

`catch` blocks are checked **in order**. Catch the most specific first
(`NumberFormatException` is a subtype of `IllegalArgumentException`).

## 4. `try`-with-resources — auto-close

Anything implementing `AutoCloseable` (which extends `Closeable`) is
auto-closed at the end of the block, **even if an exception is thrown**.

```java
try (var in = Files.newBufferedReader(path);
     var out = Files.newBufferedWriter(target)) {
    in.transferTo(out);
}      // no finally; in.close() and out.close() called automatically
```

You can declare multiple resources; they're closed in *reverse* order of
declaration.

To make your own resource participate:
```java
public final class ConnectionPool implements AutoCloseable {
    @Override public void close() { /* release */ }
}
```

## 5. Suppressed exceptions

If the try block throws and the close also throws, the close exception
is **suppressed** (not lost):
```java
try (var r = new Resource()) { ... }
// if r throws, then close() throws, the close() exception is
// retrieved via try { ... } catch (Throwable t) { t.addSuppressed(...); }
```
Most code never needs to deal with this. If you write your own
`AutoCloseable`, throw the primary exception and let `addSuppressed` be
called automatically.

## 6. Custom exceptions

A well-designed custom exception:
- Is `final` (don't let anyone extend and re-throw as something else).
- Has a `serialVersionUID` (if you ever serialise it; many do even if
  they don't think they will).
- Provides a constructor that takes a `cause`.
- Provides a constructor that takes a message and a `cause`.

```java
public final class ServiceException extends RuntimeException {
    private static final long serialVersionUID = 1L;
    public ServiceException(String message)                       { super(message); }
    public ServiceException(String message, Throwable cause)      { super(message, cause); }
}
```

A checked variant:
```java
public final class ParseException extends Exception {
    private static final long serialVersionUID = 1L;
    public ParseException(String message)                  { super(message); }
    public ParseException(String message, Throwable cause) { super(message, cause); }
}
```

## 7. When *not* to use exceptions

- **Don't use exceptions for control flow.** Catching and re-throwing
  in a loop is slow and ugly. Return an `Optional` or a sum type
  instead.
- **Don't swallow exceptions.** An empty `catch` block hides bugs. If
  you really must, log and continue — and document it.
- **Don't return `null` instead of throwing** when the situation is
  unexpected. Throwing makes the failure visible.

```java
// BAD: returning null on "not found"
public User findUser(long id) {
    return users.get(id);  // could be null
}

// GOOD: throw if the precondition is "id must exist"
public User requireUser(long id) {
    User u = users.get(id);
    return Objects.requireNonNull(u, () -> "user not found: " + id);
}
```

## 8. `Optional<T>` — the empty-result type

Use it for **return types** when:
- The empty case is **expected** (lookup by id, parsing optional config).
- The caller is **forced to handle the empty case**.

```java
public Optional<User> findUser(long id) { /* ... */ }

User u = findUser(42).orElseThrow();                        // throws NoSuchElementException
String name = findUser(42).map(User::name).orElse("(none)");
findUser(42).ifPresentOrElse(this::greet, () -> log("miss"));
```

**Don't use `Optional` for:**
- Fields (it doesn't serialise cleanly and adds noise to the type).
- Parameters (it forces the caller to wrap every value; use a default
  value or overload instead).
- Collection elements (an `Optional<List<X>>` is silly; the empty list
  *is* the empty case).

## 9. `Optional` vs. exceptions vs. null

| Use | When |
|-----|------|
| `Optional<T>` return | The empty case is expected and routine (lookup, parse, config) |
| Checked exception | External failure the caller might recover from (I/O, parse) |
| Unchecked exception | Precondition violation or unrecoverable bug |
| `null` | Almost never. If you have to, document the hell out of it. |

## 10. A worked example — a parser

```java
public final class IntParser {

    public static OptionalInt tryParse(String s) {           // returns empty on no parse
        if (s == null) return OptionalInt.empty();
        try {
            return OptionalInt.of(Integer.parseInt(s.trim()));
        } catch (NumberFormatException e) {
            return OptionalInt.empty();
        }
    }

    public static int parseOrThrow(String s) {               // throws on no parse
        return tryParse(s).orElseThrow(() ->
            new IllegalArgumentException("not an int: " + s));
    }
}
```

Two methods, two contracts: a "soft" one that returns empty, and a
"strict" one that throws. The caller picks.

## 11. Logging (preview)

A quick mention — in real code you'll log exceptions:
```java
} catch (IOException e) {
    log.error("failed to read {}", path, e);   // SLF4J — pass the throwable as the last argument
    throw new ServiceException("read failed", e);
}
```
**Never** call `e.printStackTrace()` in production code. Use a logger.

---

## Do the lab

Build a small `IntParser` and a `try`-with-resources `FileCopier` that
uses both. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

`Throwable` · `Error` · `Exception` · `RuntimeException` · checked vs.
unchecked · `try`/`catch`/`finally` · `try`-with-resources ·
`AutoCloseable` · `Closeable` · suppressed exception · custom exception ·
`Optional` · `OptionalInt`/`OptionalLong`/`OptionalDouble` · logging

**Next →** [Module 09: Enums, Nested & Inner Classes](../09-enums-nested/)
