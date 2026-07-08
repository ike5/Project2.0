# Module 01 — Java Fast-Track for Spring

**Goal:** learn the Java features that Spring Boot code *actually* uses — fast.
No exhaustive language tour, no applet history — just the language you'll read
and write starting next module.

⏱️ ~2.5 hours · 🎯 Prereq: Module 00 complete (JDK 21 + IDE working).

> This module is **denser than the rest**. It teaches just enough Java to read
> Spring's source code and write idiomatic Spring code. Skip it only if you
> already write Java comfortably; otherwise do every exercise.

---

## 1. The shape of a Java program

A Java program is a collection of classes. The entry point is a `public static
void main(String[] args)` method. Everything lives inside a class — no
top-level functions, no top-level constants.

```java
package com.example.greeter;            // folder: com/example/greeter/

public class Greeter {                   // file: Greeter.java
    public static void main(String[] args) {
        System.out.println("Hello, " + args[0]);
    }
}
```

Run it:
```bash
javac com/example/greeter/Greeter.java   # produces Greeter.class
java -cp . com.example.greeter.Greeter world
# → Hello, world
```

**Conventions:**
- One top-level public class per file, named after the file.
- Package names are all lowercase, dot-separated: `com.example.greeter`.
- Class names are `PascalCase`; variables and methods are `camelCase`.
- Constants are `UPPER_SNAKE_CASE`.

---

## 2. Types, primitives, and `String`

Java is statically typed. Eight primitive types:

| Type | Size | Example | Default |
|------|------|---------|---------|
| `boolean` | 1 bit | `true` | `false` |
| `byte` | 8 bits | `0` | `0` |
| `short` | 16 bits | `0` | `0` |
| `int` | 32 bits | `42` | `0` |
| `long` | 64 bits | `42L` | `0L` |
| `float` | 32 bits | `3.14f` | `0.0f` |
| `double` | 64 bits | `3.14` | `0.0d` |
| `char` | 16 bits | `'a'` | `'\0'` |

Everything else is a **reference type** (objects). `String` is a reference
type, not a primitive — but it has language-level syntax (`"hello" + " world"`).

```java
String name = "ann";
int    age  = 30;
double gpa  = 3.9;
boolean active = true;
```

> **Immutability:** `String` is immutable. `"a" + "b"` creates a new `String`.
> For lots of concatenation, use `StringBuilder`.

---

## 3. Records — the data class you'll use everywhere

Spring controllers receive and return JSON. The cleanest Java type for "a
bunch of fields" is a **record** (Java 16+):

```java
public record Task(String title, String description, boolean done) { }

Task t = new Task("buy milk", "2% organic", false);
t.title();          // "buy milk"   — accessor, not a getter
t.done();           // false
```

Records give you:
- A constructor with all fields.
- One accessor per field (`title()`, not `getTitle()`).
- `equals`, `hashCode`, `toString` for free.
- Immutability.

> **Spring tip:** records make great DTOs. They serialize to/from JSON
> cleanly with Jackson (the default JSON library in Spring Boot).

---

## 4. Collections — `List`, `Set`, `Map`

Java's collections are interfaces in `java.util`:

```java
import java.util.*;

List<String> names = new ArrayList<>();   // ordered, allows duplicates
Set<String> tags   = new HashSet<>();     // unordered, unique
Map<String, Integer> ages = new HashMap<>();  // key → value

names.add("ann");
ages.put("ann", 30);
```

**Immutability:** prefer immutable collections for return values:
```java
List<String> readOnly = List.of("ann", "bob", "cat");
Map<String, Integer> ages = Map.of("ann", 30, "bob", 25);
```

**Iterating:**
```java
for (String n : names) System.out.println(n);
```

---

## 5. Lambdas and the Stream API

Java 8 added **lambdas** (anonymous functions) and the **Stream API** for
functional-style collection processing. You'll see both all over Spring code.

```java
List<Task> tasks = List.of(
    new Task("buy milk",  "...", false),
    new Task("fix bug",   "...", true),
    new Task("write docs","...", false)
);

// filter + map + collect
List<String> openTitles = tasks.stream()
    .filter(t -> !t.done())                  // lambda
    .map(Task::title)                        // method reference
    .toList();                               // Java 16+ (returns immutable list)

// forEach
tasks.forEach(t -> System.out.println(t.title()));
```

**Key stream operations:**
- `filter(predicate)` — keep elements matching a predicate.
- `map(function)` — transform each element.
- `sorted(comparator)` — sort.
- `distinct()` — deduplicate.
- `limit(n)`, `skip(n)` — slice.
- `collect(Collectors.toList())` / `.toList()` — terminal.
- `forEach(consumer)` — terminal.

**Method references** are a shorthand for a lambda that calls a single method:
- `Task::title` ≡ `t -> t.title()`
- `System.out::println` ≡ `x -> System.out.println(x)`

---

## 6. `Optional` — handling values that may be absent

`Optional<T>` is a container that may or may not hold a `T`. It replaces
`null` in many places.

```java
Optional<Task> maybe = repo.findById(42L);

String title = maybe
    .map(Task::title)               // Optional<Task> → Optional<String>
    .orElse("default");             // unwrap or fall back

maybe.ifPresent(t -> System.out.println(t.title()));
```

> **Don't:** use `Optional` as a field type or as a method parameter. It's
> designed for return values.

---

## 7. Exceptions — checked vs unchecked

Java has two kinds of exceptions:

- **Checked** — subclasses of `Exception` (not `RuntimeException`). The
  compiler forces you to handle them with `try`/`catch` or `throws`. Example:
  `java.io.IOException`.
- **Unchecked** — subclasses of `RuntimeException`. You *may* handle them, but
  you don't have to. Example: `NullPointerException`, `IllegalArgumentException`.

```java
try {
    Path p = Path.of("/etc/hosts");
    String s = Files.readString(p);
} catch (IOException e) {              // checked → must catch or throws
    log.error("read failed", e);
    throw new RuntimeException(e);     // wrap and rethrow
}
```

**Spring's pattern:** define your own unchecked exceptions for business
problems (`TaskNotFoundException extends RuntimeException`) and translate
them to HTTP responses in `@ControllerAdvice` (Module 06).

**`try`-with-resources** for anything that implements `AutoCloseable`:
```java
try (var conn = dataSource.getConnection();
     var stmt = conn.prepareStatement("...")) {
    // ...
}   // conn and stmt auto-closed even if an exception is thrown
```

---

## 8. Generics — type parameters

Generics let you parameterize a class by a type:

```java
public class Box<T> {
    private final T value;
    public Box(T value) { this.value = value; }
    public T get() { return value; }
}

Box<String> stringBox = new Box<>("hi");
String s = stringBox.get();      // no cast needed
```

Spring uses generics heavily in repositories and `RestTemplate`/`WebClient`
responses: `List<Task>`, `Optional<User>`, `ResponseEntity<Task>`.

**Wildcards:**
- `List<? extends Task>` — a list of some subtype of `Task` (read-only).
- `List<? super Task>` — a list of some supertype of `Task` (write-safe).

---

## 9. Interfaces and default methods

Interfaces in modern Java can have:
- Abstract methods (the contract).
- `default` methods (concrete implementations).
- `static` methods.

```java
public interface Notifier {
    void notify(String message);

    default void notifyAll(List<String> messages) {
        messages.forEach(this::notify);
    }
}
```

Spring's `JpaRepository` is a great example: a long interface hierarchy with
many default methods (`save`, `findById`, `delete`, …) that your repository
inherits for free.

---

## 10. Annotations — metadata the compiler and frameworks read

Annotations attach metadata to classes, methods, fields, and parameters.
Spring is built on them.

```java
@Override                                    // compiler check
public String toString() { return "..."; }

@Deprecated(since = "2.0", forRemoval = true)
public void oldMethod() { }
```

Custom annotations:
```java
@Retention(RetentionPolicy.RUNTIME)           // available at runtime
@Target(ElementType.METHOD)                   // only on methods
public @interface Timed { String value() default ""; }
```

> **Spring tip:** every `@RestController`, `@GetMapping`, `@Entity` is an
> annotation. Module 02 onwards you'll see them constantly.

---

## 11. The `var` keyword (Java 10+)

`var` lets the compiler infer the local variable type. It's *not* dynamic
typing — the type is fixed at compile time.

```java
var list = new ArrayList<String>();   // ArrayList<String>
var map  = Map.of("a", 1, "b", 2);    // Map<String, Integer>
```

> **Spring tip:** use `var` for readability when the right-hand side makes
> the type obvious, especially with `ResponseEntity<...>` and generic
> streams.

---

## 12. Modules, classpath, and the build tool

You won't ship one `.java` file in this course — you'll ship a **JAR** built
by **Maven** (or Gradle). Maven's `pom.xml`:

- Declares the **project coordinates** (group, artifact, version).
- Lists **dependencies** (Spring, Jackson, …) — Maven downloads them.
- Defines **build phases**: `compile`, `test`, `package`, `install`.

```bash
mvn compile   # compile sources
mvn test      # compile + run tests
mvn package   # build a JAR in target/
mvn spring-boot:run  # run the app
```

The JAR Maven produces is **executable** (Module 02 shows the magic line):
```bash
java -jar target/app-0.0.1-SNAPSHOT.jar
```

---

## 13. What you **don't** need to know yet

This module deliberately omits a lot. You can read and write Spring Boot code
without:

- Reflection (Spring uses it, you don't need to).
- Classpath / classloader internals.
- `equals` / `hashCode` contracts in depth.
- The module system (`module-info.java`) — Spring Boot apps don't use it.
- Concurrency primitives beyond `CompletableFuture` (Module 11).
- Java 21 features beyond what we covered: virtual threads (Module 09 mentions
  them in a "production tip" box), pattern matching in `switch` (rarely used
  in Spring code today), sealed types.

When you encounter them, learn them on demand.

---

## 14. Do the lab

Get fluent in the language: write a small console program that uses records,
lists, streams, lambdas, `Optional`, exceptions, and the build tool. You'll
re-read this code in Module 02 and recognize every feature in Spring.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

JVM · JDK · class · record · lambda · stream · Optional · checked exception · generic · annotation · `var` · Maven

**Next →** [Module 02: Spring Boot Fundamentals](../02-spring-boot-fundamentals/)
