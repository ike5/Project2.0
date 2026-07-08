# OOP Cheatsheet

The vocabulary of object-oriented programming in Java, with the Java-specific
bits called out.

## The four principles

| Principle | Java answer |
|-----------|------------|
| **Encapsulation** | `private` fields, methods that enforce invariants, defensive copies. |
| **Abstraction** | Interfaces, abstract classes, `default` methods. |
| **Inheritance** | `extends` (single class) + `implements` (any number of interfaces). |
| **Polymorphism** | Method overriding + dynamic dispatch. |

## Visibility

| Modifier | Same class | Same package | Subclass | Anywhere |
|----------|:----------:|:------------:|:--------:|:--------:|
| `private` | ✅ | ❌ | ❌ | ❌ |
| *package-private* (no modifier) | ✅ | ✅ | ❌ | ❌ |
| `protected` | ✅ | ✅ | ✅ | ❌ |
| `public` | ✅ | ✅ | ✅ | ✅ |

> **Tip:** `protected` is over-used. It creates a maintenance liability
> (subclasses can depend on your internals). Prefer package-private + careful
> package boundaries.

## Class shape (cheat layout)

```java
public class MyClass {                 // class header

    // 1. static fields
    public static final int MAX = 100;
    private static int count = 0;

    // 2. instance fields (final wherever possible)
    private final String name;
    private final int id;

    // 3. constructors
    public MyClass(String name) { this(name, nextId()); }
    public MyClass(String name, int id) { this.name = name; this.id = id; }

    // 4. static factory methods (often preferred over public constructors)
    public static MyClass of(String name) { return new MyClass(name); }

    // 5. accessors
    public String name() { return name; }
    public int id()     { return id; }

    // 6. instance methods
    public void doWork() { /* ... */ }

    // 7. static methods
    private static synchronized int nextId() { return ++count; }

    // 8. Object overrides
    @Override public String toString()  { return "MyClass(" + name + ")"; }
    @Override public boolean equals(Object o) { /* ... */ }
    @Override public int hashCode()     { return Objects.hash(name, id); }
}
```

## Class or record or interface?

| If your type is… | Use… |
|------------------|------|
| A bundle of immutable data with no meaningful behaviour | `record` |
| A thing with state that changes over time and invariants worth enforcing | `class` (often `final`) |
| A family of related types closed at compile time (sum type) | `sealed` interface + `record`/`final class` permits list |
| A capability or contract implemented by many unrelated types | `interface` (with `default` methods for shared logic) |
| A partial implementation that subclasses share | `abstract class` |

## When to extend vs. compose

Extend only when:
- The subclass **is-a** the parent in the Liskov sense (you can substitute it
  anywhere the parent is used).
- You need the parent's *type*, not just some of its behaviour.

Otherwise, **compose**: take a `Strategy` field, a `Decorator` wrapper, a
`Builder` parameter.

## `equals` / `hashCode` / `toString` rules

- **Always override both `equals` and `hashCode`.** Two objects that are
  `equals` must have the same `hashCode`, or `HashMap`/`HashSet` will misbehave.
- **Symmetric, reflexive, transitive, consistent, and `equals(null) == false`.**
  These are the contract; the IDE auto-generator can produce a working
  implementation, but you must check it.
- **`toString` should produce a debugging-friendly string** with the
  important fields. Don't put secrets in it; don't parse it.
- **`Comparable` types should implement `compareTo` consistent with `equals`.**
  Otherwise sorted sets and maps will misbehave.

## Immutability checklist

A truly immutable Java type:

- [ ] Class is `final` (or all fields are private and there's no public
      constructor).
- [ ] All fields are `private final`.
- [ ] No setters, no mutator methods.
- [ ] Defensive copies of mutable inputs in the constructor:
      `this.dates = List.copyOf(dates);`
- [ ] Defensive copies of mutable outputs from accessors:
      `return List.copyOf(items);`
- [ ] No `Object` methods allow the internals to leak (`clone`, etc.).

Records + `List.copyOf`/`Map.copyOf`/`Set.copyOf` give you most of this for
free.

## Design rules of thumb

- **Single responsibility:** a class should have one reason to change.
- **Open/closed:** open to extension, closed to modification. Achieved by
  polymorphism over `if`/`switch` chains on type.
- **Liskov substitution:** subtype objects must be substitutable for supertype
  objects without surprising the caller.
- **Interface segregation:** prefer many small, focused interfaces over one
  fat one. `Reader` and `Writer` are better than `IO`.
- **Dependency inversion:** depend on abstractions (interfaces), not
  concretions. Pass a `Clock`, not a `System.currentTimeMillis()` call.
