# Java Syntax Cheatsheet (for an experienced dev)

A fast reference mapping things you already know to Java 21.

## File → class → package

```java
// File: src/com/example/Hello.java
package com.example;                    // matches directory structure

public class Hello {                    // file name MUST be Hello.java
    public static void main(String[] args) {  // entry point
        System.out.println("Hello, " + args[0]);
    }
}
```

Compile + run (modern, single-file source-code launch):
```bash
javac src/com/example/Hello.java -d out
java -cp out com.example.Hello world
```

Or, since Java 11:
```bash
java Hello.java world      # single-file source-code launch
```

## Variables & types

```java
int n = 42;                  // 32-bit
long l = 42L;                // 64-bit (note L)
double d = 3.14;             // 64-bit floating
float f = 3.14f;             // 32-bit floating (note f)
boolean ok = true;           // not int
char c = 'x';                // 16-bit UTF-16 code unit
String s = "text";           // reference, immutable
var inferred = "auto";       // local type inference (still static!)
final int MAX = 100;         // constant (convention: UPPER_SNAKE)
BigDecimal money = new BigDecimal("9.99");  // for currency, never double
```

Primitives vs. wrappers:
```java
int  -> Integer   // boxing/unboxing is automatic but watch for NPEs
long -> Long
double -> Double
boolean -> Boolean
```

## Strings

```java
String name = "Ada";
String msg = "Hello, " + name + "!";                 // concatenation
String path = String.join("/", "a", "b", "c");        // join
String text = """
        Multi-line
        text block
        """;                                          // Java 15+
String fmt = "Name: %s, age: %d".formatted(name, 36); // Java 15+
String safe = "x".repeat(3);                          // "xxx"
String sub  = "hello".substring(0, 3);                // "hel"
List<String> parts = Arrays.asList("a,b,c".split(",")); // ["a","b","c"]
```

## Arrays

```java
int[] a = {1, 2, 3};
int[] b = new int[5];                  // zero-initialised
int[][] matrix = {{1, 2}, {3, 4}};     // jagged
int len = a.length;                    // array "length" is a field
for (int x : a) { System.out.println(x); }
Arrays.sort(a);                        // in-place sort
int[] copy = Arrays.copyOf(a, a.length);
List<Integer> list = Arrays.asList(1, 2, 3);   // fixed-size view
List<Integer> real  = List.of(1, 2, 3);        // immutable
```

## Collections (read [`collections.md`](./collections.md) for the full map)

```java
List<String> list   = new ArrayList<>();        // growable
List<String> immut  = List.of("a", "b");          // immutable
Set<Integer> set    = new HashSet<>();           // unique
Map<String, Integer> map = new HashMap<>();      // key -> value
Queue<String> queue = new ArrayDeque<>();        // FIFO
Deque<String> deque = new ArrayDeque<>();        // double-ended
```

## Control flow

```java
if (n > 0) { } else if (n < 0) { } else { }
for (int i = 0; i < 10; i++) { }
for (var x : list) { }                 // enhanced for
while (cond) { }
do { } while (cond);

int sign = switch (n) {                // switch EXPRESSION (Java 14+)
    case 0         -> 0;
    case 1, 2, 3   -> 1;
    default        -> -1;
};

if (obj instanceof String s) {         // pattern matching (Java 16+)
    System.out.println(s.length());
}

String result = switch (shape) {       // pattern matching for switch
    case Circle c when c.radius() > 0 -> "big circle";
    case Circle c                     -> "small circle";
    case Square s                     -> "square " + s.side();
};                                       // compiler checks exhaustiveness for sealed types
```

## Methods

```java
int add(int a, int b) { return a + b; }                  // classic
int add(int a, int b) -> a + b;                          // invalid in Java — no expression-bodied methods
static int add(int a, int b) { return a + b; }            // static method
int sum(int... xs) { int s = 0; for (int x : xs) s += x; return s; }  // varargs
```

## Classes (preview)

```java
public final class Point {                  // final: cannot be subclassed
    private final int x, y;                 // immutable fields
    public Point(int x, int y) {            // constructor
        this.x = x;
        this.y = y;
    }
    public int x() { return x; }            // accessor (no `get` prefix)
    public int y() { return y; }

    @Override
    public String toString() { return "Point(" + x + "," + y + ")"; }

    @Override
    public boolean equals(Object o) {
        return o instanceof Point p && p.x == x && p.y == y;  // pattern matching
    }
    @Override
    public int hashCode() { return Objects.hash(x, y); }
}
```

`record` (Java 16+): the above is equivalent to:
```java
public record Point(int x, int y) { }
```

## Interfaces & inheritance

```java
interface Shape {
    double area();
    default boolean isLargerThan(Shape other) { return this.area() > other.area(); }  // default method
}

class Circle implements Shape {
    private final double radius;
    Circle(double r) { this.radius = r; }
    @Override public double area() { return Math.PI * radius * radius; }
}

final class UnitCircle extends Circle {                     // inheritance
    UnitCircle() { super(1.0); }                            // super call
    @Override public double area() { return Math.PI; }      // override
}
```

Sealed hierarchy (Java 17+):
```java
public sealed interface Shape permits Circle, Square, Triangle { }
public record Circle(double radius) implements Shape { }
public record Square(double side)   implements Shape { }
public record Triangle(double base, double height) implements Shape { }
```

## Generics

```java
class Box<T> {
    private T value;
    void set(T v) { this.value = v; }
    T get() { return value; }
}

Box<String> b = new Box<>();        // diamond operator infers String
List<? extends Number> nums = List.of(1, 2.0, 3L);  // wildcard

static <T> T first(List<T> xs) { return xs.get(0); } // generic method
```

## Lambdas & streams

```java
List<String> names = List.of("ada", "alan", "grace");
List<String> upper = names.stream()
                          .map(String::toUpperCase)
                          .filter(s -> s.length() > 3)
                          .toList();                                // Java 16+
Map<Integer, List<String>> byLength = names.stream()
        .collect(Collectors.groupingBy(String::length));
```

## Exceptions

```java
try (var r = new FileReader("a.txt");        // try-with-resources (Java 7+)
     var w = new FileWriter("b.txt")) {
    r.transferTo(w);
} catch (IOException e) {
    log.warn("copy failed", e);
    throw new ServiceException("copy failed", e);   // wrap and rethrow
}
```

## Annotations

```java
@Override
public String toString() { return "Point(" + x + "," + y + ")"; }

@Deprecated(since = "21", forRemoval = true)
public void legacy() { }

@SuppressWarnings("unchecked")           // file scope: @Target(ElementType.FILE)
void raw() { var list = (List) List.of(); }
```

## Modules (JPMS, Java 9+)

```java
// module-info.java
module com.example.greeter {
    requires java.logging;                    // depend on another module
    exports com.example.greeter;              // expose a package
}
```

## Concurrency preview

```java
CompletableFuture<String> f = CompletableFuture
        .supplyAsync(() -> fetchSomething())      // runs on ForkJoinPool
        .thenApply(String::toUpperCase)           // transform
        .exceptionally(ex -> "fallback");          // recover

String result = f.get(5, TimeUnit.SECONDS);      // or compose further
```

---

## Idioms worth memorising

- **`@Override` always.** The compiler checks your claim.
- **`equals` + `hashCode` together** — or use a record.
- **Prefer `List.of`/`Map.of`/`Set.of`** for immutable literals.
- **Prefer `ArrayDeque` over `LinkedList`** for queues/stacks.
- **Prefer `BigDecimal` for money,** never `double`.
- **Prefer `final` everywhere** as a default for fields, parameters, and
  classes that aren't meant to be extended.
- **Prefer composition over inheritance** unless you're explicitly modelling
  an *is-a* relationship.
- **Prefer records** for data carriers; write classes when behaviour and
  invariants matter.
- **Prefer `Optional<T>` for return types**; never for fields or parameters.
- **Prefer streams** for declarative transformations, but `for` loops for
  complex local mutation.
