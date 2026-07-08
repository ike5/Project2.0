# Glossary

Every important term in the course, defined in plain English. Terms appear in
the order they become relevant.

---

## Phase 0 — Foundations

**JDK (Java Development Kit)** — the toolchain you need to *write and compile*
Java: the compiler (`javac`), the standard library, the documentation tool,
and the JRE. To run Java code you can also use a JRE alone.

**JRE (Java Runtime Environment)** — what you need to *run* a Java program:
the JVM plus the standard library. In modern Java (since Java 11) a JRE is
just a subset of the JDK.

**JVM (Java Virtual Machine)** — the program that actually executes your
Java bytecode. It's why Java is "write once, run anywhere": the same
`.class` files run on any compliant JVM. The JVM JIT-compiles hot bytecode
to native code at runtime, manages memory via a garbage collector, and
enforces the security/sandbox model.

**Bytecode** — the intermediate, platform-independent instruction set
(`.class` files) that `javac` produces. The JVM interprets or JIT-compiles
this to native code.

**JIT (Just-In-Time) compilation** — the JVM's trick of compiling hot
bytecode paths to native code at runtime, so well-warm code runs near the
speed of C++.

**Garbage collector (GC)** — the JVM subsystem that automatically reclaims
memory occupied by objects no longer reachable from your code. You cannot
explicitly free memory in Java (no `free()` or `delete`); you only *create*
objects.

**Source file** — a `.java` file you write.

**Class file** — a `.class` file `javac` produces, containing bytecode for
exactly one public type. Its name must match the public type.

**Package** — a namespace for types. `java.util.List` and `com.example.MyList`
don't collide because they're in different packages. Packages also map to
directory structure: `com/example/MyList.java`.

**JAR (Java ARchive)** — a ZIP file with a `.jar` extension bundling `.class`
files and resources, optionally with a `META-INF/MANIFEST.MF`. The standard
way to ship libraries and applications.

**Module** — a JAR with a `module-info.class` (compiled from
`module-info.java`) that declares which packages it `requires` and which it
`exports`. JPMS, added in Java 9, lets you build truly encapsulated libraries
beyond class-path JARs.

**Classpath** — the list of directories and JARs the JVM searches for types
when running in the legacy mode. Replaced by the module path in modular
applications, but still in use.

**`main` method** — the entry point the JVM invokes: `public static void
main(String[] args)`.

---

## Phase 1 — OOP fundamentals

**Class** — a blueprint describing the data (fields) and behaviour (methods)
of a kind of thing. You `new` a class to get an instance.

**Object / instance** — a concrete thing created from a class, living on the
heap.

**Field** — a variable that holds state, declared inside a class (also called
"instance variable" or "attribute"). Each object has its own copy.

**Method** — a function attached to a class.

**Constructor** — a special method that runs when you `new` a class, used to
initialise the object's state. Has no return type and is named after the
class.

**`this`** — a reference to the current object — useful for disambiguating
fields from parameters and for passing the current object to other code.

**`static`** — a class-level member that belongs to the class itself, not to
any instance. Shared across all instances; one per class.

**Encapsulation** — the practice of hiding an object's internal state behind
methods so that invariants can be enforced. The single most important OOP
principle in practice.

**Accessor / getter** — a method that returns the value of a private field.

**Mutator / setter** — a method that changes a private field, often
performing validation.

**Immutability** — the property of an object whose state cannot change after
construction. Immutability is hugely valuable for reasoning, concurrency, and
defensive copying.

**`final`** — a modifier meaning "this variable's reference can't change" or
"this class can't be extended" or "this method can't be overridden",
depending on context.

**`record`** — a special class form (Java 16+) that auto-generates
constructors, accessors, `equals`, `hashCode`, and `toString` for an
immutable bundle of fields. Use records for "data with no identity beyond
its fields."

**Inheritance** — the `extends` relationship: a subclass inherits fields and
methods from its superclass. Java supports single inheritance of classes.

**Subclass / superclass** — the "child" and "parent" in an inheritance
relationship.

**Method overriding** — a subclass providing a new implementation of a method
declared in its superclass. The method must have the same signature; the
return type can be a *covariant* subtype.

**Polymorphism** — the property that a reference of type `Animal` can hold
any subtype and the *actual* method invoked is the subclass's override.
"Many shapes" — the same call behaves differently depending on the actual
object.

**Dynamic dispatch / late binding** — the JVM's mechanism for picking which
overridden method to call, decided at runtime from the actual object's class.

**`super`** — a reference to the parent class, used to call the parent's
constructor (`super(...)`) or methods (`super.foo()`).

**Abstract class** — a class you can't instantiate directly, only subclass.
Used to define a partial implementation and force subclasses to fill in
abstract methods. Declared with `abstract`.

**Abstract method** — a method declaration with no body, forcing subclasses
to provide one.

**Concrete class** — any class that is not abstract; can be instantiated.

**Interface** — a contract listing abstract methods (and, since Java 8,
default and static methods) that an implementing class must provide. A
class can implement any number of interfaces. Since Java 8 interfaces often
replace abstract classes for type-only contracts.

**`@Override`** — an annotation that asserts "this method overrides a parent."
If it doesn't, the code won't compile. Always use it.

**`Object`** — the root class of every class in Java. If you write
`class Foo {}` it's really `class Foo extends Object`. `equals`, `hashCode`,
`toString`, and a few others are declared on `Object`.

**`equals` and `hashCode`** — methods every well-behaved class must override
together. Used by hash-based collections (`HashMap`, `HashSet`) and by
testing/assertion code.

**`toString`** — a debugging-friendly string representation. The debugger,
loggers, and IDEs all call it.

**Sealed class / interface** — a class or interface that restricts which
classes may extend or implement it (`permits`). Forces the hierarchy to be
known and exhaustively handled in `switch` expressions.

**Pattern matching for `instanceof`** — `if (obj instanceof Cat c) { c.meow();
}`. The variable `c` is in scope and non-null in the truthy branch. Avoids
the old two-step cast.

**Pattern matching for `switch`** — `switch (shape) { case Circle c -> ...;
case Square s -> ...; }`. The compiler checks exhaustiveness for sealed
hierarchies.

**Covariant return type** — an override can narrow the return type to a
subtype of the parent's declared type. `Animal.clone()` may return
`Shepherd` if `Shepherd extends Animal`.

**`package-private`** — the default visibility in Java (no modifier). Visible
only to types in the same package. The most under-used and most useful
visibility for OOP.

---

## Phase 2 — Type system & data

**Generic** — a class, interface, or method parameterised over a type.
`List<String>` is a `List` of strings. Generics are the Java type system's
most powerful safety feature.

**Type parameter** — the placeholder, e.g. `T` in `List<T>`. Conventional
names: `T` (type), `E` (element), `K`/`V` (key/value), `R` (return), `N`
(number).

**Bound** — a constraint on a type parameter: `<T extends Comparable<T>>`
means `T` must be a subtype of `Comparable<T>`.

**Wildcard `?`** — "an unknown type" used in generic method calls and
declarations. `? extends T` (an unknown subtype) and `? super T` (an unknown
supertype).

**PECS** — "producer extends, consumer super." A mnemonic: use `? extends T`
when you only *read* `T` values from a structure, and `? super T` when you
only *write* `T` values into it. Wild, Joshua Bloch, *Effective Java*.

**Type erasure** — the JVM does not know about your generic type parameters
at runtime; they exist only in the compiler. `List<String>` and `List<Integer>`
are the same class at runtime. This has consequences: no `new T()`, no
`instanceof List<String>`.

**Raw type** — using a generic type without type parameters (`List` instead
of `List<String>`). Compiles with a warning; loses type safety. Avoid.

**Collection** — the root interface of the Java Collections Framework
(`java.util`). Subtypes include `List`, `Set`, `Queue`, `Deque`.

**`List`** — an ordered, indexable collection. Implementations: `ArrayList`
(default, fast random access), `LinkedList` (cheap insert/remove at ends).

**`Set`** — a collection with no duplicates. Implementations: `HashSet`
(constant-time, unordered), `LinkedHashSet` (insertion-ordered),
`TreeSet` (sorted).

**`Map`** — a key/value mapping. Implementations: `HashMap` (default,
constant-time), `LinkedHashMap` (insertion-ordered), `TreeMap` (sorted by
key).

**`Queue` / `Deque`** — FIFO / double-ended queue. Implementations:
`ArrayDeque` (preferred), `LinkedList`, `PriorityQueue` (heap-ordered).

**Comparator** — an object that knows how to compare two values for
ordering. `Comparator.naturalOrder()`, `Comparator.reverseOrder()`, or your
own lambda.

**Comparable** — the interface a class implements to declare its natural
order: `int compareTo(T other)`.

**Iterator / `Iterable`** — anything you can `for-each` over.

**Lambda** — an anonymous function value. `x -> x * 2`. Lambdas are *not*
classes you write; the compiler converts them to implementations of a
functional interface.

**Functional interface** — an interface with exactly one abstract method.
The target type for lambdas. Examples: `Runnable`, `Callable`,
`Comparator<T>`, `Function<T,R>`, `Consumer<T>`, `Supplier<T>`,
`Predicate<T>`.

**Method reference** — `String::length` is shorthand for `s -> s.length()`.
`::` binds to either an instance method (`s::toString`), a static method
(`Math::abs`), or a constructor (`ArrayList::new`).

**Stream** — a lazy, declarative pipeline of operations on a sequence of
values. Composed of intermediate operations (return a stream, e.g. `map`,
`filter`) and a terminal operation (returns a value or side-effect, e.g.
`collect`, `forEach`).

**`Collector`** — an object that knows how to reduce a stream's elements
into a result (a list, a map, a sum, a grouping). The standard ones are in
`java.util.stream.Collectors`.

**Optional** — a container that may or may not hold a non-null value. A
replacement for returning `null`. Use it for *return types*; don't use it
for fields or as a parameter type.

**Exception** — an object representing an error condition, thrown with
`throw` and caught with `try`/`catch`.

**Checked exception** — a subclass of `Exception` (but not `RuntimeException`)
that the compiler forces you to handle or declare. Examples:
`IOException`, `SQLException`.

**Unchecked exception** — a subclass of `RuntimeException`. The compiler
doesn't require handling. Examples: `NullPointerException`,
`IllegalArgumentException`.

**Error** — a serious problem the application isn't expected to handle
(`OutOfMemoryError`, `StackOverflowError`). Don't catch these.

**`try`-with-resources** — a `try` statement (`try (var r = ...; ) { }`)
that auto-closes any `AutoCloseable` resource. Replaces the classic
`finally { close(); }` boilerplate.

**`AutoCloseable`** — the interface for things that can be closed (sockets,
streams, JDBC connections). Implement it on your resource types.

**Enum** — a type whose values are a fixed, named set. Java enums are far
richer than C's: each constant can have fields, methods, and its own
behaviour.

**Static nested class** — a class defined inside another class, marked
`static`. Behaves like a top-level class for access purposes.

**Inner class** — a non-static nested class; each instance has an implicit
reference to its enclosing instance. Use sparingly; usually a sign that
the inner class should be a top-level type.

**Local class** — a class declared inside a method. Rare; prefer lambdas.

**Anonymous class** — a one-off class declared and instantiated in a single
expression (`new Runnable() { ... }`). Replaced by lambdas in most modern
code.

---

## Phase 3 — Modern Java, concurrency & design

**Annotation** — a marker (`@Override`, `@Deprecated`, custom). Either
compile-time (the compiler checks for it), build-time (a tool processes it),
or runtime (reflection reads it).

**`@Retention`** — declares *when* an annotation is available: `SOURCE`,
`CLASS`, or `RUNTIME`.

**`@Target`** — declares *where* an annotation can be applied: `METHOD`,
`FIELD`, `TYPE`, etc.

**Reflection** — the JVM's ability to inspect and manipulate classes,
fields, and methods at runtime, via `Class`, `Method`, `Field`, and
`Constructor` objects. Powerful but slow, brittle, and unsafe (bypasses
generics). Use it sparingly: frameworks, libraries, testing.

**`var`** — a local-variable type inference keyword (Java 10+). `var list =
new ArrayList<String>();` — the compiler infers the type. Use when it
improves readability; don't use it when the type isn't obvious from the
right-hand side.

**Text block** — a multi-line string literal delimited by `"""` (Java 15+).
Great for JSON, SQL, HTML.

**Thread** — a single, independent path of execution within a JVM process.

**`Runnable` / `Callable<T>`** — tasks for threads: `Runnable` runs and
returns nothing; `Callable` returns a value and may throw.

**`ExecutorService`** — a high-level API for managing thread pools. Always
prefer it over creating raw threads.

**`CompletableFuture<T>`** — a composable, asynchronous result. `thenApply`,
`thenCompose`, `thenCombine` build pipelines; `supplyAsync`/`runAsync` run
on the common pool.

**Thread safety** — the property that a class behaves correctly when used
by multiple threads concurrently. The main techniques are: immutability,
confinement, synchronization, and atomic types.

**Race condition** — a bug where the outcome depends on the unpredictable
interleaving of concurrent operations. Test with tools like
`ThreadSanitizer`, but in practice the fix is usually "make it immutable."

**`synchronized`** — a monitor-based mutual-exclusion keyword. Use
`ConcurrentHashMap` and `java.util.concurrent` before reaching for
`synchronized`.

**`volatile`** — guarantees that reads/writes to a field are visible across
threads (no caching in registers). Does **not** make compound operations
atomic.

**Atomic types** — `AtomicInteger`, `AtomicReference<T>`, etc. CAS-based
lock-free counters and references.

**Locks** — `ReentrantLock` and friends. More flexible than `synchronized`
(try-lock, timed, interruptible).

**Immutability for safety** — the most important concurrency technique.
A truly immutable object can be freely shared between threads.

**`Path` / `Paths`** — the modern (NIO.2) way to represent filesystem
paths. Replaces `java.io.File` for new code.

**`Files`** — utility methods on `Path`: read, write, copy, walk the
directory tree.

**Stream of lines** — `Files.lines(path)` returns a `Stream<String>` of the
file's lines. Combine with streams for declarative file processing.

**`Serializable`** — the marker interface that says "this object can be
turned into bytes and back." Easy to use, hard to use *correctly*:
versioning, security, performance all bite. Prefer JSON or Protobuf for
new APIs.

**`transient`** — a field modifier meaning "skip this when serialising."

**JPMS (Java Platform Module System)** — the platform's module system
introduced in Java 9. A modular JAR declares its dependencies and exports
explicitly in `module-info.java`.

**`requires` / `exports`** — module directives: `requires` declares a
dependency; `exports` declares a package visible to other modules.

**`jlink`** — a JDK tool that builds a custom JRE containing *only* the
modules your application needs. Result: a tiny, app-specific runtime you
can ship.

**`jpackage`** — a JDK tool that bundles that custom JRE with your
application into a native installer (`.dmg`, `.msi`, `.deb`).

---

## Phase 4 — Design patterns

**Strategy** — define a family of algorithms, encapsulate each, and make
them interchangeable. In modern Java, a `@FunctionalInterface` + a field
or constructor parameter.

**Decorator** — wrap an object to add behaviour dynamically. Java's I/O
streams are the canonical example; in modern code prefer composition with
a default-method interface.

**Builder** — a step-by-step construction API for objects with many
optional fields. Replaces telescoping constructors.

**Factory** — a method that creates instances, hiding the concrete type.
Use it when the implementation might vary, or for namespaced
construction.

**Observer** — a one-to-many dependency: when one object changes state,
all its dependents are notified. In modern Java, `Consumer<T>` or
`PropertyChangeListener`.

**Adapter** — translate one interface to another. The single-method
`@FunctionalInterface` adapter (`event -> ...`) is everywhere.

**Singleton** — a class with exactly one instance. The *modern* Java
singleton is a `record` with a private static field, or an `enum` (the
best singleton form).

**SOLID** — the five design principles: Single responsibility,
Open-closed, Liskov substitution, Interface segregation, Dependency
inversion. (The course touches these throughout; this glossary gives the
acronym for reference.)
