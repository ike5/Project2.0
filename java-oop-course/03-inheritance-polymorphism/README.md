# Module 03 — Inheritance, Polymorphism & Abstract Classes

**Goal:** model "is-a" relationships with `extends` and `abstract`, use
**polymorphism** to write extensible code, and learn when *not* to inherit.

⏱️ ~2.5 h · 🎯 Prereq: Module 02.

---

## 1. The `extends` keyword

A class can `extend` exactly **one** other class. It inherits the parent's
fields and methods and can override the methods it disagrees with.

```java
public class Vehicle {
    private final String make;
    private int miles;
    public Vehicle(String make) { this.make = make; }
    public String make() { return make; }
    public int miles() { return miles; }
    public void drive(int miles) { this.miles += miles; }
    public String description() { return "%s with %d miles".formatted(make, miles); }
}

public class Car extends Vehicle {
    private final int doors;
    public Car(String make, int doors) {
        super(make);                  // call the parent constructor FIRST
        this.doors = doors;
    }
    public int doors() { return doors; }

    @Override
    public String description() {
        return "%s (%d-door car) with %d miles".formatted(make(), doors, miles());
    }
}
```

Notice:
- `super(make)` calls the parent's constructor. It must be the **first
  statement** in the subclass constructor.
- `@Override` is an annotation that **asserts** this method overrides a
  parent's. If it doesn't, the code fails to compile. *Always* use it.
- A subclass can add new fields, methods, and accessors — but it cannot
  remove or weaken anything the parent promised.

## 2. Polymorphism — the actual magic

```java
Vehicle v = new Car("Toyota", 4);
v.description();   // "Toyota (4-door car) with 0 miles"
                   // — the Car's override, picked at runtime
```

Even though the *static type* of `v` is `Vehicle`, the JVM dispatches the
call to `Car.description()` because `v` actually *is* a `Car`. This is
**dynamic dispatch** (or "late binding"), and it's the central mechanism
that makes OOP extensible.

A method that takes a `Vehicle` works for any subclass:
```java
public static void roadTrip(Vehicle v) { v.drive(100); }
roadTrip(new Car("Toyota", 4));    // fine
roadTrip(new Truck("Ford", 2000)); // fine
```

This is the *open/closed principle*: open to extension, closed to
modification. You add `Truck` without changing `roadTrip`.

## 3. Abstract classes

Sometimes a class should be *instantiable only through its subclasses*. Mark
it `abstract`. The compiler will refuse `new AbstractThing()`.

```java
public abstract class Shape {
    public abstract double area();           // no body — subclasses MUST implement
    public abstract double perimeter();

    public String describe() {               // a concrete method using the abstract ones
        return "A shape with area %.2f and perimeter %.2f".formatted(area(), perimeter());
    }
}

public final class Circle extends Shape {
    private final double radius;
    public Circle(double radius) { this.radius = radius; }
    @Override public double area()      { return Math.PI * radius * radius; }
    @Override public double perimeter() { return 2 * Math.PI * radius; }
}
```

Why use abstract classes?
- Share a partial implementation (`describe` here).
- Declare a *protocol* (the abstract methods) the subclass must fulfil.
- Capture a common type so callers can program to it (`List<Shape>`).

## 4. `Object` — what every class extends

You don't say `class Foo extends Object` because it's automatic. What you
get for free:
- `toString()` — override for debugging. Default is
  `"com.example.Foo@1f3e02a"`, which is useless.
- `equals(Object)` and `hashCode()` — override together, contract is
  reflexive/symmetric/transitive/consistent, and `equals(null) == false`.
- `getClass()` — the actual runtime class.
- `clone()`, `finalize()`, `wait()`, `notify()`, `notifyAll()` — legacy;
  usually avoid.

The `equals` contract in full:
- *Reflexive*: `x.equals(x) == true`.
- *Symmetric*: `x.equals(y) == y.equals(x)`.
- *Transitive*: if `x.equals(y)` and `y.equals(z)`, then `x.equals(z)`.
- *Consistent*: repeated calls return the same value (assuming no state
  change).
- `x.equals(null) == false`.

## 5. Liskov substitution — the L of SOLID

> *Objects of a superclass shall be replaceable with objects of a subclass
> without breaking the application.*

This sounds obvious. In practice, it constrains your overrides:

- A subclass method may **accept the same inputs** (`parameters`).
- It may **return the same or a more specific** type (covariant return).
- It may **not throw new checked exceptions** that the parent didn't
  declare.
- It may **not strengthen preconditions** (e.g. reject inputs the parent
  accepts).
- It may **not weaken postconditions** (e.g. return `null` when the parent
  promises a value).

```java
class Bird { void fly() { /* ... */ } }        // parent says: I fly
class Penguin extends Bird {                    // Liskov violation!
    @Override void fly() { throw new UnsupportedOperationException(); }
}
```
The fix is usually a *better model*: `abstract class Bird`, with
`abstract class FlyingBird extends Bird` and `Penguin extends Bird` directly.
*Don't* let the type hierarchy overstate what every subtype can do.

## 6. When to extend (and when not to)

**Extend** when:
- The subclass **is-a** the parent in the Liskov sense.
- You need access to the parent's *type*, not just its behaviour.

**Don't extend** when:
- You only want to *reuse* a few methods. Use composition (a field of the
  parent type) instead.
- You're inheriting just to override one method. The interface (Module 04)
  is almost always a better answer.
- You want to *combine* behaviours. Use multiple interfaces or the
  Decorator pattern (Module 14).

```java
// Inheritance done right:
class SavingsAccount extends BankAccount { ... }      // a savings account IS-A bank account

// Inheritance done wrong:
class BankAccount2 extends ArrayList<Transaction> { }  // an account is NOT a list
```

## 7. Covariant return types

An override can narrow the return type to a subtype of the parent's
declared return. This is one place Java is more flexible than, say, C++:

```java
class Animal { Animal clone() { /* ... */ } }
class Sheep extends Animal {
    @Override Sheep clone() { /* ... */ }    // legal — Sheep IS-A Animal
}
```

The compiler lets you do this because the *caller's* contract is satisfied
(they get an `Animal` either way) and the *subclass's* contract is
stronger (it always gets a `Sheep`).

## 8. `final` methods and `final` classes

- A `final` method **cannot be overridden** by subclasses. Useful for
  invariants: any subclass *must* call your implementation, not bypass it.
- A `final` class **cannot be extended** at all. Use it whenever you can
  — it makes the class easier to reason about.

```java
public final class String { /* ... */ }      // can't subclass String
public class HttpClient {
    public final void close() { /* ... */ }   // subclasses must use this implementation
}
```

`String` is `final` so that you can't write a `BadString` that breaks the
JVM's interning or `String` constant pool invariants.

## 9. A worked example

```java
abstract class Employee {
    private final String name;
    private final BigDecimal baseSalary;
    public Employee(String name, BigDecimal baseSalary) {
        this.name = Objects.requireNonNull(name);
        this.baseSalary = Objects.requireNonNull(baseSalary);
    }
    public String name()             { return name; }
    public BigDecimal baseSalary()    { return baseSalary; }
    public abstract BigDecimal monthlyPay();
    public BigDecimal annualPay()    { return monthlyPay().multiply(BigDecimal.valueOf(12)); }
}

final class SalariedEmployee extends Employee {
    public SalariedEmployee(String name, BigDecimal base) { super(name, base); }
    @Override public BigDecimal monthlyPay() { return baseSalary(); }
}

final class HourlyEmployee extends Employee {
    private final int hoursPerMonth;
    public HourlyEmployee(String name, BigDecimal rate, int hours) {
        super(name, rate);
        this.hoursPerMonth = hours;
    }
    @Override public BigDecimal monthlyPay() {
        return baseSalary().multiply(BigDecimal.valueOf(hoursPerMonth));
    }
}

// Use polymorphism:
BigDecimal payroll(List<Employee> staff) {
    return staff.stream()
                .map(Employee::monthlyPay)
                .reduce(BigDecimal.ZERO, BigDecimal::add);
}
```

Adding a new employee type (`CommissionedEmployee`) requires *no* changes
to `payroll`. That's the power of polymorphism.

---

## Do the lab

Build a small `Shape` hierarchy in `com.example.shapes` and exercise
polymorphism. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms

`extends` · inheritance · subclass / superclass · method overriding · `@Override` ·
polymorphism · dynamic dispatch · abstract class · `Object` · Liskov
substitution · covariant return · `final` class / method

**Next →** [Module 04: Interfaces, Records & Sealed Types](../04-interfaces-records-sealed/)
