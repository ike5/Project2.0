# Challenge 07 — Factory pattern

Solutions in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Implement `MyLinkedList`** in `07-factory-pattern/code/linked_list_mine.py` from scratch. Submit to LeetCode 707.
2. **Build a `Shape` factory** in `07-factory-pattern/code/shape_factory.py`:
   - `Shape` base with an `area()` method (raises `NotImplementedError`).
   - `Square(side)`, `Circle(radius)`, `Rectangle(w, h)`, each with their own `area()`.
   - `Shape.from_dict({"kind": "circle", "radius": 5})` that returns the right shape. Add three more cases.
3. **Write `pytest` tests** in `07-factory-pattern/code/test_mine.py`.

## Success criteria

- [ ] LeetCode 707 accepts your `MyLinkedList`.
- [ ] `Shape.from_dict({"kind": "square", "side": 4}).area() == 16`.
- [ ] `Shape.from_dict({"kind": "circle", "radius": 1}).area() == pytest.approx(3.14159, rel=0.01)`.
- [ ] All tests pass.
