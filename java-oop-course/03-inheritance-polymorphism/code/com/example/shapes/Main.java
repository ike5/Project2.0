package com.example.shapes;

import java.util.List;

public class Main {
    public static void main(String[] args) {
        List<Shape> shapes = List.of(
            new Circle(2.0),
            new Rectangle(3.0, 4.0),
            new Circle(1.5)
        );

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
