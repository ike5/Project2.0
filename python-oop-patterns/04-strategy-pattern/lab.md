# Lab 04 — Strategy pattern

**You'll:** build a `TaxCalculator` that takes a strategy, try several strategy flavors, and then implement a `BrowserHistory` from LeetCode 1472. ⏱️ ~30 min.

---

## Part A — TaxCalculator with a function strategy

```bash
python 04-strategy-pattern/code/tax.py
```

✅ You should see:

```
flat(1500)         = 225.0
progressive(1500)  = 250.0
zero(1500)         = 0.0
lambda 10%(500)    = 50.0
```

Four strategies, same class. The class is `TaxCalculator`; the algorithms are functions and a lambda.

## Part B — Try a class with `__call__`

Open `04-strategy-pattern/code/tax_callable.py`. There's a `Bracket` class with a `__call__` method. Try passing *two* brackets in a list and averaging the result. (Just experiment in the REPL — no test required.)

## Part C — BrowserHistory

```bash
python 04-strategy-pattern/code/browser_history.py
```

✅ You should see a sequence of URLs as you `visit` and `back` and `forward`.

Read the implementation. Note the `self._back` and `self._forward` lists — they use `list.pop()` (which pops from the *end* in O(1)) to avoid O(n) front-popping.

## Part D — pytest

```bash
python -m pytest 04-strategy-pattern/code/test_browser_history.py
```

✅ All tests pass.

---

When everything passes, move to the challenge.
