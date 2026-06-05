// Reference solution for Challenge 02.
using System;

// 1. Shape hierarchy
public abstract class Shape
{
    public abstract double Area();
    public virtual string Describe() => $"{GetType().Name}: area={Area():0.00}";
}
public class Circle(double radius) : Shape
{
    public override double Area() => Math.PI * radius * radius;
}
public class Rectangle(double width, double height) : Shape
{
    protected double Width { get; } = width;
    protected double Height { get; } = height;
    public override double Area() => Width * Height;
}
// Square reuses Rectangle via inheritance.
public class Square(double side) : Rectangle(side, side)
{
    public override string Describe() => $"Square(side): area={Area():0.00}";
}

// 2. Value object
public record Temperature(double Celsius)
{
    public double Fahrenheit => Celsius * 9 / 5 + 32;
    public Temperature With(double celsius) => this with { Celsius = celsius };
}

// 3. Strategy via interface
public interface IDiscount { decimal Apply(decimal total); }
public class PercentOff(decimal percent) : IDiscount
{
    public decimal Apply(decimal total) => total * (1 - percent / 100m);
}
public class FixedOff(decimal amount) : IDiscount
{
    public decimal Apply(decimal total) => Math.Max(0, total - amount);
}
public class Checkout(IDiscount discount)
{
    public decimal Total(decimal subtotal) => discount.Apply(subtotal);
}

// 4. Enum + parse
public enum ShippingSpeed { Standard, Express, Overnight }
public static class Shipping
{
    public static int DeliveryDays(ShippingSpeed speed) => speed switch
    {
        ShippingSpeed.Standard => 5,
        ShippingSpeed.Express => 2,
        ShippingSpeed.Overnight => 1,
        _ => throw new ArgumentOutOfRangeException(nameof(speed)),
    };
}

public static class Challenge02
{
    public static void Demo()
    {
        Shape[] shapes = [new Circle(2), new Rectangle(3, 4), new Square(5)];
        foreach (var s in shapes) Console.WriteLine(s.Describe());

        var t = new Temperature(100);
        Console.WriteLine($"{t.Celsius}C = {t.Fahrenheit}F; equal={t == new Temperature(100)}");

        Console.WriteLine(new Checkout(new PercentOff(10)).Total(200));  // 180
        Console.WriteLine(new Checkout(new FixedOff(30)).Total(200));    // 170

        Console.WriteLine(Shipping.DeliveryDays(ShippingSpeed.Express)); // 2
    }
}
