package com.example.shapes;

public abstract class Shape {
    public abstract double area();
    public abstract double perimeter();

    public final String describe() {
        return "%s: area=%.4f, perimeter=%.4f"
                .formatted(name(), area(), perimeter());
    }

    protected abstract String name();
}
