# Challenge 02 — Design with Objects

Solution in [`solutions/`](./solutions/). Try first.

## Tasks
1. **Shape hierarchy.** Define an abstract `Shape` with `abstract double Area()` and a
   `virtual string Describe()`. Implement `Circle`, `Rectangle`, and `Square` (reuse
   `Rectangle` via inheritance or composition). Print each shape's description from an
   array of `Shape`.

2. **Value object.** Create a `record Temperature(double Celsius)` with a computed
   `Fahrenheit` property and a `With(double celsius)` that returns a new value. Show
   value equality.

3. **Strategy via interface.** Define `interface IDiscount { decimal Apply(decimal total); }`
   with two implementations (`PercentOff`, `FixedOff`). Write a `Checkout` that takes
   an `IDiscount` and applies it. Demonstrate swapping strategies without changing `Checkout`.

4. **Enum + parse.** Model `enum ShippingSpeed { Standard, Express, Overnight }` and a
   method that maps each to a delivery-days estimate using a switch expression.

## Success criteria
- [ ] Polymorphic `Shape[]` prints correct areas/descriptions.
- [ ] `Temperature` is immutable with a correct `Fahrenheit` and value equality.
- [ ] `Checkout` works with either discount strategy, unchanged.
- [ ] Enum mapping covers all cases (and rejects undefined values).
