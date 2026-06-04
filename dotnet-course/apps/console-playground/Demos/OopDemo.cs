namespace ConsolePlayground.Demos;

/// <summary>Module 02: classes, records, interfaces, polymorphism.</summary>
public static class OopDemo
{
    public static void Run()
    {
        // Polymorphism through an abstract base + overrides.
        Shape[] shapes = [new Circle(2), new Rectangle(3, 4)];
        foreach (var shape in shapes)
            Console.WriteLine($"{shape.GetType().Name} area = {shape.Area():0.00}");

        // Records: immutable value-equality data types.
        var p1 = new Money("USD", 9.99m);
        var p2 = p1 with { Amount = 19.99m };   // non-destructive mutation
        Console.WriteLine($"records: p1={p1}, p2={p2}, equal={p1 == p2}");

        // Interface-based design.
        IGreeter greeter = new FriendlyGreeter();
        Console.WriteLine(greeter.Greet("Grace"));
    }
}

public abstract class Shape
{
    public abstract double Area();
}

// Primary constructor (C# 12).
public class Circle(double radius) : Shape
{
    public override double Area() => Math.PI * radius * radius;
}

public class Rectangle(double width, double height) : Shape
{
    public override double Area() => width * height;
}

public record Money(string Currency, decimal Amount);

public interface IGreeter
{
    string Greet(string name);
}

public class FriendlyGreeter : IGreeter
{
    public string Greet(string name) => $"Hello, {name}! 👋";
}
