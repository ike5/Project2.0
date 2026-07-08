package com.example.shapes;

import java.util.List;
import java.util.Objects;

public final class Challenge03 {

    private Challenge03() {}

    public static void main(String[] args) {
        // 1. Liskov violation: a 'MutableRectangle' allows width and height to be set
        //    independently. The Square subclass forces them to be equal — but a caller
        //    who holds a Rectangle reference can still call setWidth(3) and then
        //    get a Rectangle that is *not* a square. The contract of Rectangle
        //    (width and height are independent) is broken.
        MutableRectangle r = new Square(2.0);
        System.out.println("after construct: " + r);            // 2x2
        r.setWidth(3.0);
        System.out.println("after setWidth(3): " + r);          // 3x2 — NOT a square!
        // A caller expecting a Rectangle invariant (w == h) is surprised.
        // The fix is to make Rectangle's fields final and not provide mutators;
        // the violation is then no longer expressible.

        // 2. Animal chorus.
        List<Animal> zoo = List.of(
                new Dog("Rex"),
                new Cat("Whiskers"),
                new Duck("Quack")
        );
        System.out.println("---");
        System.out.println(Animal.chorus(zoo));

        // 3. Covariant return.
        Dog d = new Dog("Buddy");
        Dog copy = d.clone();
        System.out.println("cloned: " + copy.name());

        // 4. Parrot just slots in.
        List<Animal> withParrot = List.of(
                new Dog("Rex"),
                new Cat("Whiskers"),
                new Duck("Quack"),
                new Parrot("Polly")
        );
        System.out.println(Animal.chorus(withParrot));
    }

    // -------- 1. Mutable rectangle (no 'final' fields) and broken Square --------
    public static class MutableRectangle {
        private double width, height;
        public MutableRectangle(double width, double height) {
            this.width = width; this.height = height;
        }
        public double width()  { return width; }
        public double height() { return height; }
        public void setWidth(double w)  { this.width = w; }
        public void setHeight(double h){ this.height = h; }
        @Override public String toString() { return "%.1fx%.1f".formatted(width, height); }
    }

    public static final class Square extends MutableRectangle {
        public Square(double side) { super(side, side); }
        // No overrides! setWidth/setHeight come straight from the parent. The
        // result: a caller with a Rectangle reference can mutate one dimension
        // and break the "is a square" promise. This is the Liskov violation:
        // Square IS-A Rectangle (mathematically), but it isn't safe to use in
        // place of a mutable Rectangle.
    }

    // -------- 2. Animal hierarchy --------
    public abstract static class Animal {
        private final String name;
        protected Animal(String name) { this.name = Objects.requireNonNull(name); }
        public String name()             { return name; }
        public abstract String speak();
        public String introduce()        { return "%s says %s".formatted(name, speak()); }
        public Animal clone()            { try { return (Animal) super.clone(); }
                                            catch (CloneNotSupportedException e) {
                                                throw new AssertionError(e); } }
        public static String chorus(List<Animal> zoo) {
            return zoo.stream().map(Animal::introduce).reduce("", (a, b) -> a + b + "\n").trim();
        }
    }
    public static final class Dog extends Animal {
        public Dog(String name) { super(name); }
        @Override public String speak() { return "woof"; }
        @Override public Dog clone()     { return new Dog(name()); }   // covariant return
    }
    public static final class Cat extends Animal {
        public Cat(String name) { super(name); }
        @Override public String speak() { return "meow"; }
        @Override public Cat clone()     { return new Cat(name()); }
    }
    public static final class Duck extends Animal {
        public Duck(String name) { super(name); }
        @Override public String speak() { return "quack"; }
        @Override public Duck clone()    { return new Duck(name()); }
    }

    // -------- 4. New type, no other code changes --------
    public static final class Parrot extends Animal {
        public Parrot(String name) { super(name); }
        @Override public String speak() { return "hello"; }
    }
}
