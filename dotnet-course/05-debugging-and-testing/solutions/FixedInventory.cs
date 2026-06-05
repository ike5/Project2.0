// Reference fix for the Lab 05 bugs.
using System.Collections.Generic;
using System.Linq;

namespace Lab05;

public record Item(string Name, decimal Price, int Quantity);

public class Inventory
{
    private readonly List<Item> _items = new();

    public void Add(Item item) => _items.Add(item);

    // FIX 1: guard the empty case instead of letting Average throw.
    public decimal AveragePrice() => _items.Count == 0 ? 0m : _items.Average(i => i.Price);

    // FIX 2: sum price * quantity across all items.
    public decimal TotalValue() => _items.Sum(i => i.Price * i.Quantity);

    // (Challenge task 3)
    public void Remove(string name)
    {
        var item = _items.FirstOrDefault(i => i.Name == name)
            ?? throw new KeyNotFoundException(name);
        _items.Remove(item);
    }
}
