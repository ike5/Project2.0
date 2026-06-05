// A small class with a planted bug for Lab 05. Drop into a console project.
// Symptom: AveragePrice() throws on an empty inventory, and TotalValue() is wrong
// when an item has zero quantity. Use the debugger to confirm, then fix (see solutions/).
using System.Collections.Generic;
using System.Linq;

namespace Lab05;

public record Item(string Name, decimal Price, int Quantity);

public class Inventory
{
    private readonly List<Item> _items = new();

    public void Add(Item item) => _items.Add(item);

    // BUG 1: throws InvalidOperationException ("Sequence contains no elements") if empty.
    public decimal AveragePrice() => _items.Average(i => i.Price);

    // BUG 2: uses Count of items, not the sum of (price * quantity).
    public decimal TotalValue() => _items.Count * _items.First().Price;
}
