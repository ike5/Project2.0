# Module 10 — Annotations, Reflection & Modern Sugar

**Goal:** read and write Java annotations, use reflection sparingly,
and wield the modern syntactic sugar (`var`, text blocks, multi-line
strings) that makes modern Java pleasant.

⏱️ ~2 h · 🎯 Prereq: Module 09.

---

## 1. Annotations

An annotation is a marker that the compiler, a build tool, or your code
can read. The simplest:
```java
@Override
public String toString() { return "..."; }
```

`@Override` is **built-in**: the compiler checks that this method
overrides a parent. Other built-ins: `@Deprecated`, `@SuppressWarnings`,
`@FunctionalInterface`, `@SafeVarargs`.

## 2. Built-in annotations

```java
@Override                               // assert override
@Deprecated(since = "21", forRemoval = true)
public void legacy() { /* ... */ }

@SuppressWarnings("unchecked")
void rawCast() { var list = (List) List.of(); }

@FunctionalInterface
interface Transformer<I, O> { O transform(I input); }
```

## 3. Declaring a custom annotation

```java
import java.lang.annotation.*;

@Retention(RetentionPolicy.RUNTIME)         // visible at runtime
@Target(ElementType.METHOD)                 // can go on methods
public @interface Timed {
    String unit() default "ms";
}
```

The meta-annotations are themselves annotations:
- `@Retention` — `SOURCE` (compiler only), `CLASS` (in `.class` but not
  runtime), `RUNTIME` (readable via reflection).
- `@Target` — where it can go (`TYPE`, `FIELD`, `METHOD`, `PARAMETER`,
  `CONSTRUCTOR`, `LOCAL_VARIABLE`, `TYPE_USE`, `TYPE_PARAMETER`,
  `MODULE`, `RECORD_COMPONENT`).

## 4. Using a custom annotation

```java
public final class Report {
    @Timed(unit = "ns")
    public int compute() { return 42; }

    @Timed          // default unit is "ms"
    public int slow() { return 1; }
}
```

Annotations with no methods are *marker* annotations. With one method,
they often look like properties (`@Timed(unit = "ns")`).

## 5. Reading annotations with reflection

```java
Method m = Report.class.getMethod("compute");
Timed t = m.getAnnotation(Timed.class);
if (t != null) {
    System.out.println("unit: " + t.unit());
}
```

Reflection is slow, brittle, and bypasses generics — **use it only for
frameworks and tooling**. For your everyday logic, design with
interfaces, not annotations.

## 6. Reflection — when you must

Reflection lets you:
- Inspect a class: `Class.forName("com.example.Foo")`,
  `Foo.class.getMethods()`, `Foo.class.getFields()`.
- Invoke a method: `Method.invoke(receiver, args)`.
- Read a field: `Field.get(instance)`.
- Construct an object: `Constructor.newInstance(args)`.

```java
Object o = Class.forName("java.util.ArrayList").getDeclaredConstructor().newInstance();
((List<?>) o).add("hi");
System.out.println(o);    // [hi]
```

**Gotchas:**
- `setAccessible(true)` bypasses `private` (and the module system).
- Generics are erased: `List<String>` is just `List` at runtime.
- Methods that take primitive `int` vs `Integer` matter.
- Performance: reflection is ~10x slower than a direct call.

## 7. `var` — local type inference

```java
var list = new ArrayList<String>();         // inferred as ArrayList<String>
var map  = Map.of("a", 1, "b", 2);          // inferred as Map<String, Integer>
var path = Path.of("/tmp/x");               // inferred as Path
```

`var` is a *local-variable* feature only. The type is still static —
the compiler infers it from the right-hand side. The byte code is
identical to writing the type explicitly.

**Use it when:**
- The right-hand side makes the type obvious.
- The variable's name documents the value (`customers` is better than
  `List<Customer> customers`).

**Don't use it when:**
- The right-hand side is `null` (`var x = null;` won't compile).
- The type is the *documentation* (public method signatures — but you
  can't use `var` there anyway).
- Numeric literals (`var x = 42;` is `int`; `var x = 42L;` is `long`).

## 8. Text blocks (Java 15+)

A multi-line string literal. The opening `"""` is followed by a
newline, and the closing `"""` is on its own line.

```java
String json = """
        {
          "name": "Ada",
          "age":  36
        }""";
```

The compiler:
- Strips the common leading whitespace (the "indentation").
- Preserves newlines.
- Lets you use `"` and `\` without escaping (most of the time).

`\s` is a *real* escape that includes trailing whitespace, so
`"line1 \s"` keeps the trailing space.

## 9. Other modern sugar

- **Pattern matching for `instanceof`** (Module 01) — `if (obj instanceof String s)`.
- **Pattern matching for `switch`** (Module 04) — `case CardPayment c ->`.
- **Records** (Module 04) — `record Point(int x, int y)`.
- **Sealed types** (Module 04) — `sealed interface X permits ...`.
- **Text blocks** (above).
- **`var`** (above).
- **`@Override` on records** — for overriding record-component accessors
  (rare, but legal).
- **Helpful NPEs** — NPEs in Java 21+ tell you *which* variable was null,
  not just the line number. A small but very real productivity boost.

## 10. A worked example — a tiny `Json` round-trip

This is **not** a real JSON parser (use Jackson for that), but it shows
the elements:

```java
record Person(String name, int age) {}

String toJson(Person p) {
    return """
        {
          "name": "%s",
          "age":  %d
        }""".formatted(p.name(), p.age());
}

Person fromJson(String s) {
    // Extremely naive — for illustration only.
    String name = s.lines()
            .filter(l -> l.contains("name"))
            .findFirst().orElseThrow()
            .split(":")[1].trim().replaceAll("[\",]", "");
    int age = Integer.parseInt(
            s.lines().filter(l -> l.contains("age")).findFirst().orElseThrow()
             .split(":")[1].trim().replaceAll("[, ]", ""));
    return new Person(name, age);
}
```

The point isn't the JSON; it's the *combination* of `record` + text block
+ `.lines()` + `String.formatted`.

---

## Do the lab

Build a custom `@Timed` annotation and a small processor that uses
reflection to read it. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

annotation · `@Override` / `@Deprecated` / `@SuppressWarnings` /
`@FunctionalInterface` · `@Retention` · `@Target` · marker annotation ·
reflection · `Class` · `Method` · `Field` · `setAccessible` · `var` ·
text block · helpful NPE

**Next →** [Module 11: Concurrency Essentials](../11-concurrency/)
