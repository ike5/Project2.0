# Lab 03 — Encapsulation

**You'll:** see all three levels of encapsulation, build a property, and use the validated `BankAccount`. ⏱️ ~30 min.
Run from the `python-oop-course/` folder with your venv active.

---

## Part A — Run the encapsulation levels demo

```bash
python 03-encapsulation/code/encapsulation_levels.py
```

✅ You should see that `_value` is readable but flagged as "internal," and `__value` is hidden behind name mangling. The script will show you the actual mangled name.

## Part B — Run the property demo

```bash
python 03-encapsulation/code/property_demo.py
```

✅ You should see:

```
c.radius = 2.0   c.area = 12.566
trying to set c.area to 999 ...
AttributeError: property 'area' of 'Circle' object has no setter
```

And a `Celsius` example that raises `ValueError` for `-300` and accepts `-50`.

## Part C — Use the validated `BankAccount`

```bash
python 03-encapsulation/code/bank_account_v2.py
```

✅ Try assigning a negative balance in a REPL:

```bash
python -i 03-encapsulation/code/bank_account_v2.py
```

```python
>>> a = BankAccount("Ana", 100)
>>> a.balance
100
>>> a.balance = -5
ValueError: balance must be >= 0
>>> a.balance = 200     # this one works
>>> a.balance
200
```

✅ Negative assignments should raise; positive ones should succeed.

## Cleanup

Nothing to clean up.

## What you learned

- A single leading underscore is a convention; a double leading underscore is name-mangled.
- `@property` lets you add validation or computation without breaking the call sites.
- A property with only a getter is read-only.
- Assigning to a property's setter from inside `__init__` is a clean way to validate at construction.

➡️ **[challenge.md](./challenge.md)** then [Module 04: Inheritance](../04-inheritance/).
