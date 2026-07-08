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
