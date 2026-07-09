# Lab 03 — Sliding Window

**You'll:** solve *Best Time to Buy and Sell Stock* (a one-element window)
and *Longest Substring Without Repeating Characters* (a variable window with a
set), in both languages. ⏱️ ~1.5 h.

---

## Part A — *Best Time to Buy and Sell Stock* in Python

```python
def max_profit(prices):
    ...


if __name__ == "__main__":
    assert max_profit([7, 1, 5, 3, 6, 4]) == 5
    assert max_profit([7, 6, 4, 3, 1]) == 0
    assert max_profit([2, 4, 1]) == 2
    print("all tests passed")
```

**Walk-through:** think of the *window* as just the running minimum price.

```python
def max_profit(prices: list[int]) -> int:
    min_price = float('inf')
    best = 0
    for p in prices:
        if p < min_price:
            min_price = p
        else:
            best = max(best, p - min_price)
    return best
```

✅ Run it.

## Part B — *Best Time to Buy and Sell Stock* in Java 21

```java
public class LabMaxProfit {
    public static int maxProfit(int[] prices) {
        // your code
    }

    public static void main(String[] args) {
        assert maxProfit(new int[]{7, 1, 5, 3, 6, 4}) == 5;
        assert maxProfit(new int[]{7, 6, 4, 3, 1}) == 0;
        assert maxProfit(new int[]{2, 4, 1}) == 2;
        System.out.println("all tests passed");
    }
}
```

**Walk-through:**

```java
public static int maxProfit(int[] prices) {
    int minPrice = Integer.MAX_VALUE;
    int best = 0;
    for (int p : prices) {
        if (p < minPrice) minPrice = p;
        else best = Math.max(best, p - minPrice);
    }
    return best;
}
```

Note `Integer.MAX_VALUE` — Java's equivalent of Python's `float('inf')`
when you only deal with integers. `MAX_VALUE + 1` is a negative number, so
be careful with `int` overflow. Here it's safe because `prices[i] <= 10^4`.

## Part C — *Longest Substring Without Repeating Characters* in Python

```python
def length_of_longest_substring(s):
    ...


if __name__ == "__main__":
    assert length_of_longest_substring("abcabcbb") == 3
    assert length_of_longest_substring("bbbbb") == 1
    assert length_of_longest_substring("pwwkew") == 3
    assert length_of_longest_substring("") == 0
    print("all tests passed")
```

**Walk-through:** maintain `[l, r)` with no repeats. When we see a repeat,
shrink from the left until the repeat is gone.

```python
def length_of_longest_substring(s: str) -> int:
    seen: set[str] = set()
    l = 0
    best = 0
    for r, c in enumerate(s):
        while c in seen:
            seen.remove(s[l])
            l += 1
        seen.add(c)
        best = max(best, r - l + 1)
    return best
```

## Part D — *Longest Substring Without Repeating Characters* in Java 21

Java's `int[128]` (or `int[256]`) for ASCII is faster than a `HashSet` here.
Each char maps to an index, and the value at that index is "the last
position where this char appeared."

```java
public class LabLongestSubstring {
    public static int lengthOfLongestSubstring(String s) {
        int[] last = new int[128];
        Arrays.fill(last, -1);
        int best = 0;
        for (int r = 0, l = 0; r < s.length(); r++) {
            char c = s.charAt(r);
            if (last[c] >= l) l = last[c] + 1;
            last[c] = r;
            best = Math.max(best, r - l + 1);
        }
        return best;
    }

    public static void main(String[] args) {
        assert lengthOfLongestSubstring("abcabcbb") == 3;
        assert lengthOfLongestSubstring("bbbbb") == 1;
        assert lengthOfLongestSubstring("pwwkew") == 3;
        assert lengthOfLongestSubstring("") == 0;
        System.out.println("all tests passed");
    }
}
```

> If the string contains Unicode (codepoints > 127) you'd need a
> `Map<Integer,Integer>`. For ASCII, `int[128]` works.

## What you learned

- The **single-pointer window state** (e.g. min price so far).
- The **set-based variable window** (e.g. characters-in-window).
- The **index-based optimization** (e.g. `last[c] = r`).
- **Java collections:** `Arrays.fill`, `int[128]`, `Math.max`.

➡️ **[challenge.md](./challenge.md)** then the [problems/](./problems/) in order.
