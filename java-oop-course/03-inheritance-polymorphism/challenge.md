# Challenge 03 — Inheritance, Polymorphism & Abstract Classes

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Liskov violation that compiles.** Write a `Square extends Rectangle`
   that *succeeds* in compiling but *violates* Liskov because the override
   mutates fields in a way that breaks the rectangle invariant. (Hint:
   you'll need a `Rectangle` whose fields are *not* `final`, with a
   `setSide`-style mutator. The `final` fields in the lab were the
   defence — the *lack* of `final` is the trap.) Then add the `final`
   modifier to the fields and re-compile: the violation becomes
   impossible. **Write a short paragraph explaining what changed.**

2. **An `Animal` hierarchy with a contract.** Define `abstract class Animal`
   with a `String speak()` abstract method, an `abstract String name()`,
   and a concrete `String introduce()`. Provide `Dog`, `Cat`, and
   `Duck` as `final` subclasses. Add a `static String chorus(List<Animal>
   zoo)` that calls `introduce()` on each. Confirm a caller of
   `Animal` can hold any of them.

3. **Covariant return.** Add a `clone()` method to `Animal` returning
   `Animal`, then override it in `Dog` to return `Dog` (covariant). Show
   in a small main that `Dog d = original.clone();` compiles without an
   explicit cast.

4. **Open/closed demonstration.** Add a `Parrot` class that *only*
   overrides `speak()` (no new fields). Show that `chorus(zoo)` works
   without modification. **Write a short paragraph explaining how this
   demonstrates the open/closed principle.**

## Success criteria

- [ ] You constructed a Liskov-violating `Square` and then removed the
      violation by making the parent's fields `final`.
- [ ] `Animal`/`Dog`/`Cat`/`Duck` and `chorus` work polymorphically.
- [ ] `Dog.clone()` returns `Dog` without a cast.
- [ ] Adding `Parrot` requires no change to `chorus`.
