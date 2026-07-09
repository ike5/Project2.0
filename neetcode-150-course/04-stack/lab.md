# Lab 04 — Stack

**You'll:** solve *Valid Parentheses* and *Daily Temperatures* in both
languages, comparing the LIFO idioms. ⏱️ ~1.5 h.

---

## Part A — *Valid Parentheses* in Python

```python
def is_valid(s):
    ...


if __name__ == "__main__":
    assert is_valid("()[]{}") is True
    assert is_valid("(]") is False
    assert is_valid("([)]") is False
    assert is_valid("{[]}") is True
    assert is_valid("") is True
    print("all tests passed")
```

**Walk-through:**

```python
def is_valid(s: str) -> bool:
    pairs = {')': '(', ']': '[', '}': '{'}
    stack: list[str] = []
    for c in s:
        if c in pairs:                       # closer
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
        else:                                # opener
            stack.append(c)
    return not stack
```

Why a `dict` for `pairs`? It's a constant-time lookup. We could also
hardcode a series of `if`s, but the dict reads cleaner.

✅ Run it.

## Part B — *Valid Parentheses* in Java 21

```java
import java.util.ArrayDeque;
import java.util.Deque;
import java.util.Map;

public class LabValidParens {
    public static boolean isValid(String s) {
        Map<Character, Character> pairs = Map.of(
            ')', '(', ']', '[', '}', '{'
        );
        Deque<Character> stack = new ArrayDeque<>();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (pairs.containsKey(c)) {
                if (stack.isEmpty() || stack.peek() != pairs.get(c)) return false;
                stack.pop();
            } else {
                stack.push(c);
            }
        }
        return stack.isEmpty();
    }

    public static void main(String[] args) {
        assert isValid("()[]{}");
        assert !isValid("(]");
        assert !isValid("([)]");
        assert isValid("{[]}");
        assert isValid("");
        System.out.println("all tests passed");
    }
}
```

`Map.of(...)` is the modern way to build an immutable map. `Map.entry(k, v)`
exists too. Both have 10-arg overloads; for more you'd use `Map.ofEntries(...)`.

`ArrayDeque` is the modern stack — `push` adds to the head, `pop` removes
from the head, `peek` reads the head.

## Part C — *Daily Temperatures* in Python

```python
def daily_temperatures(temperatures):
    ...


if __name__ == "__main__":
    assert daily_temperatures([73, 74, 75, 71, 69, 72, 76, 73]) == [1, 1, 4, 2, 1, 1, 0, 0]
    assert daily_temperatures([30, 40, 50, 60]) == [1, 1, 1, 0]
    assert daily_temperatures([90, 80, 70, 60]) == [0, 0, 0, 0]
    print("all tests passed")
```

**Walk-through:** the *monotonic decreasing* stack.

```python
def daily_temperatures(temperatures: list[int]) -> list[int]:
    n = len(temperatures)
    answer = [0] * n
    stack: list[int] = []   # indices, with decreasing temperatures
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            answer[j] = i - j
        stack.append(i)
    return answer
```

Note: the stack stores **indices**, not temperatures. We need the index to
write the answer `i - j`.

## Part D — *Daily Temperatures* in Java 21

```java
import java.util.ArrayDeque;
import java.util.Arrays;
import java.util.Deque;

public class LabDailyTemperatures {
    public static int[] dailyTemperatures(int[] temperatures) {
        int n = temperatures.length;
        int[] answer = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();   // indices, decreasing temps
        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && temperatures[stack.peek()] < temperatures[i]) {
                int j = stack.pop();
                answer[j] = i - j;
            }
            stack.push(i);
        }
        return answer;
    }

    public static void main(String[] args) {
        System.out.println(Arrays.toString(
            dailyTemperatures(new int[]{73, 74, 75, 71, 69, 72, 76, 73})));
        System.out.println(Arrays.toString(
            dailyTemperatures(new int[]{30, 40, 50, 60})));
    }
}
```

## What you learned

- **LIFO matching** for parentheses and similar structures.
- **Monotonic stack** for "next greater" — O(n) instead of O(n²).
- **Java's modern stack** is `ArrayDeque`; never use `java.util.Stack`.
- **Indices, not values, in the stack** — we need them to compute the answer.

➡️ **[challenge.md](./challenge.md)** then the [problems/](./problems/) in order.
