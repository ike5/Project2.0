# Lab 03 — A `Shape` Hierarchy

**You'll:** model a small OOP domain with inheritance, polymorphism, and
abstract classes. ⏱️ ~50 min.

---

## Part A — Set up

```bash
mkdir -p ~/dev/oop03 && cd ~/dev/oop03
mkdir -p src/com/example/shapes
```

## Part B — The hierarchy

`src/com/example/shapes/Shape.java` (abstract base):
```java
package com.example.shapes;

public abstract class Shape {
    public abstract double area();
    public abstract double perimeter();

    public final String describe() {        // final: subclasses can't override this
        return "%s: area=%.4f, perimeter=%.4f"
                .formatted(name(), area(), perimeter());
    }
    protected abstract String name();
}
```

`src/com/example/shapes/Circle.java`:
```java
package com.example.shapes;

public final class Circle extends Shape {
    private final double radius;
    public Circle(double radius) {
        if (radius <= 0) throw new IllegalArgumentException("radius must be > 0");
        this.radius = radius;
    }
    public double radius() { return radius; }
    @Override public double area()      { return Math.PI * radius * radius; }
    @Override public double perimeter() { return 2 * Math.PI * radius; }
    @Override protected String name()    { return "Circle(r=" + radius + ")"; }
}
```

`src/com/example/shapes/Rectangle.java`:
```java
package com.example.shapes;

public final class Rectangle extends Shape {
    private final double width, height;
    public Rectangle(double width, double height) {
        if (width <= 0 || height <= 0) {
            throw new IllegalArgumentException("width/height must be > 0");
        }
        this.width = width;
        this.height = height;
    }
    public double width()  { return width; }
    public double height() { return height; }
    @Override public double area()      { return width * height; }
    @Override public double perimeter() { return 2 * (width + height); }
    @Override protected String name()    { return "Rectangle(" + width + "x" + height + ")"; }
}
```

Notice:
- `Shape` is `abstract` and can't be `new`'d.
- `Circle` and `Rectangle` are `final` — no further inheritance.
- `name()` is `protected` — only subclasses implement it. (Module 04 will
  show how `toString` belongs on `Object` and `name` is better as a
  `public String kind()` accessor.)

## Part C — Driver

`src/com/example/shapes/Main.java`:
```java
package com.example.shapes;

import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<Shape> shapes = List.of(
            new Circle(2.0),
            new Rectangle(3.0, 4.0),
            new Circle(1.5)
        );

        // Polymorphism: each shape's actual type is used.
        shapes.forEach(s -> System.out.println(s.describe()));

        System.out.println("---");
        System.out.println("Total area: " + totalArea(shapes));
        System.out.println("Largest: "    + largest(shapes).describe());
    }

    public static double totalArea(List<Shape> shapes) {
        return shapes.stream().mapToDouble(Shape::area).sum();
    }

    public static Shape largest(List<Shape> shapes) {
        return shapes.stream().max((a, b) -> Double.compare(a.area(), b.area()))
                     .orElseThrow();
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.shapes.Main
```

Expected:
```
Circle(r=2.0): area=12.5664, perimeter=12.5664
Rectangle(3.0x4.0): area=12.0000, perimeter=14.0000
Circle(r=1.5): area=7.0686, perimeter=9.4248
---
Total area: 31.6350
Largest: Circle(r=2.0): area=12.5664, perimeter=12.5664
```

✅ The drivers `totalArea` and `largest` work on `Shape` — they don't know
or care which concrete subclass. That's polymorphism.

## Part D — Add a `Square` and a `Triangle`

Add `Square extends Rectangle` and `Triangle extends Shape`. Notice that a
square *is-a* rectangle, so it can subclass; a triangle is a separate
shape and must implement the abstract methods. Run `Main` again with these
added — no other code needs to change.

> Reflection: this is the *open/closed principle* in action. You extended
> the system (new shapes) without modifying the existing code (the
> drivers).

## Part E — Break it (Liskov)

To *see* the Liskov rule, try this:

```java
class SneakySquare extends Rectangle {
    public SneakySquare(double side) { super(side, side); }
    @Override public void setWidth(double w)  { /* sneaky */ }
}
```

Wait — `Rectangle` has `final` fields, so you can't subclass and override
its `width`/`height`. **That's deliberate.** Marking fields `final` and
the class itself `final` is how Java classes defend their invariants. Try
removing `final` from `Rectangle`'s fields and you can write the broken
subclass. Then add it back and notice you can't.

## What you learned

- `extends` for "is-a"; composition for "uses-a" or "has-a."
- `abstract` classes declare a contract subclasses must fulfil.
- Polymorphism: code that takes a `Shape` works for any subclass.
- Liskov substitution: a subclass must be substitutable for the parent.
- `final` classes and `final` fields defend invariants.

➡️ **[challenge.md](./challenge.md)** then [Module 04](../04-interfaces-records-sealed/).
