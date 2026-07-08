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
