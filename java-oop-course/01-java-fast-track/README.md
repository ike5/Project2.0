# Module 01 — Java Fast-Track

**Goal:** get fluent in the Java syntax, types, and control flow you'll use
in every later module. You already program — this is brisk and
contrast-driven.

⏱️ ~2 h · 🎯 Prereq: Module 00.

---

## 1. Two kinds of types

- **Primitives** — `int`, `long`, `double`, `boolean`, `char`, `byte`,
  `short`, `float`. They hold their data *directly* and are passed by
  value (copied). Eight total.
- **Reference types** — `String`, arrays, every class, every interface.
  The variable holds a *reference* to an object on the heap; assignment
  copies the reference, not the object.

```java
int a = 1;
int b = a;            // copy
b = 2;
System.out.println(a); // 1 — a is unchanged

int[] xs1 = {1, 2, 3};
int[] xs2 = xs1;      // same reference
xs2[0] = 99;
System.out.println(xs1[0]);  // 99 — xs1 and xs2 point to the same array
```

This explains "why did my change to one variable affect another?" — reference
sharing. `String` is a reference type but **immutable** — every "modification"
makes a new string.

Primitives have **wrapper types** (`Integer`, `Long`, ...) for when a
reference is required (collections, generics, `Optional`).

## 2. Reference equality vs. value equality

- `==` on reference types checks **identity**: are these the same object?
- `.equals(...)` checks **value**: does this object *claim* to be equal to
  that one?

```java
String a = new String("hi");
String b = new String("hi");
a == b;           // false — different objects
a.equals(b);      // true  — same value
```

For `String` and the boxed primitives, prefer `equals`. `==` is for primitives
and identity ("is this the same map entry?").

## 3. Control flow (with modern twists)

```java
if/else, for, foreach, while, do/while  // as you'd expect

// switch EXPRESSION (Java 14+) — returns a value:
String size = switch (n) {
    case 0           -> "zero";
    case 1, 2, 3     -> "small";
    case Integer i when i < 0 -> "negative " + i;     // guarded case
    default          -> "big";
};

// pattern matching with 'instanceof' (Java 16+):
if (obj instanceof String s && s.length() > 3) {  // s is in scope, non-null
    System.out.println(s.toUpperCase());
}

// enhanced for:
for (var x : List.of(1, 2, 3)) { /* ... */ }
```

`switch` on enums and sealed types is *exhaustive* — the compiler will tell
you if you missed a case (Module 04).

## 4. Methods

```java
int add(int a, int b) { return a + b; }              // classic
void log(String msg) { /* ... */ }
int sum(int... xs) { int s = 0; for (int x : xs) s += x; return s; }  // varargs

static int factorial(int n) {                        // static
    if (n < 0) throw new IllegalArgumentException("negative");
    return n <= 1 ? 1 : n * factorial(n - 1);
}
```

There is no expression-bodied method syntax in Java (yet) — `int add(int a,
int b) -> a + b;` is not legal. Use a one-liner with `return`.

Arguments to **primitive** params are copied; to **reference-type** params,
the *reference* is copied (so you can mutate the object, but reassigning the
param doesn't affect the caller).

## 5. Strings you'll actually use

```java
String s = "name=%s, age=%d".formatted(name, age);            // printf style
String path = String.join("/", "a", "b", "c");                 // join
String upper = "hello".toUpperCase();
String trimmed = "  hi  ".trim();
List<String> parts = "a,b,c".split(",");                      // ["a","b","c"]
String csv = String.join(",", parts);
boolean blank = "".isBlank();                                 // whitespace check
String repeated = "ab".repeat(3);                             // "ababab"

String json = """
        {
          "name": "Ada",
          "age":  36
        }
        """;                                                   // text block (Java 15+)
```

Prefer `String.format`-style **placeholders over concatenation** for any
non-trivial string; the compiler optimises both, but the formatted version
reads better.

## 6. Arrays vs. collections

Arrays are low-level, fixed-size, covariant (`String[]` is an `Object[]`),
and reify their element type only at runtime. The **Collections Framework**
(Module 06) is what you reach for in 99% of cases.

```java
int[] fixed = {1, 2, 3};                          // primitive array
String[] ss = new String[]{"a", "b"};
List<String> list = new ArrayList<>(List.of("a", "b"));   // growable
List<String> immut = List.of("a", "b");                    // immutable
```

## 7. `null` — the billion-dollar mistake

`null` is a valid value for any reference type. Reading a field or calling
a method on `null` throws `NullPointerException`. Java 21+ provides
**nullness analysis** through JSpecify and tools (SpotBugs, Error Prone, IDE
inspections) but not the language itself — yet.

Until then, the discipline is:

- **Be explicit about who can return `null`.** Document it, or return
  `Optional<T>` (Module 08).
- **Validate parameters** in constructors and public methods:
  `Objects.requireNonNull(name, "name")`.
- **Avoid `null` in collections** unless you have a real reason. `List.of`
  and `Map.of` reject nulls.

```java
public class User {
    private final String name;
    public User(String name) {
        this.name = Objects.requireNonNull(name, "name");
    }
    public String name() { return name; }
}
```

## 8. A taste of `var`

Java 10 added **local type inference**:

```java
var list = new ArrayList<String>();   // inferred as ArrayList<String>
var map  = Map.of("a", 1, "b", 2);     // inferred as Map<String, Integer>
```

`var` is *not* `dynamic` — the type is still statically determined at
compile time. Use it when the right-hand side makes the type obvious; avoid
it when the type *is* the documentation (public method signatures, complex
generics).

---

## Do the lab

Compile a few programs that exercise types, strings, control flow, and
`null`-safety. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

primitive · reference type · wrapper · boxing · `==` vs. `equals` · switch
expression · pattern matching for `instanceof` · varargs · text block · `var`

**Next →** [Module 02: OOP Foundations](../02-oop-foundations/)
