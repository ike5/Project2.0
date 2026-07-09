# Lab 10 — Backtracking

**You'll:** implement *Subsets* and *Permutations* in both languages. ⏱️ ~1 h.

---

## Part A — *Subsets* in Python

```python
def subsets(nums):
    out = []
    def backtrack(i, path):
        # your code
        ...
    backtrack(0, [])
    return out


if __name__ == "__main__":
    got = sorted([sorted(s) for s in subsets([1, 2, 3])])
    expected = [[], [1], [2], [3], [1, 2], [1, 3], [2, 3], [1, 2, 3]]
    assert got == sorted([sorted(s) for s in expected])
    print("all tests passed")
```

**Walk-through:**

```python
def subsets(nums):
    out = []
    def backtrack(i, path):
        if i == len(nums):
            out.append(path.copy())
            return
        # skip nums[i]
        backtrack(i + 1, path)
        # include nums[i]
        path.append(nums[i])
        backtrack(i + 1, path)
        path.pop()
    backtrack(0, [])
    return out
```

The include/skip recursion produces 2^n subsets. We `path.copy()` so the
recorded subset doesn't get clobbered by later backtracking.

## Part B — *Subsets* in Java 21

```java
import java.util.ArrayList;
import java.util.List;

public class LabSubsets {
    public static List<List<Integer>> subsets(int[] nums) {
        List<List<Integer>> out = new ArrayList<>();
        backtrack(out, nums, 0, new ArrayList<>());
        return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] nums, int i, List<Integer> path) {
        if (i == nums.length) {
            out.add(new ArrayList<>(path));
            return;
        }
        backtrack(out, nums, i + 1, path);
        path.add(nums[i]);
        backtrack(out, nums, i + 1, path);
        path.remove(path.size() - 1);
    }

    public static void main(String[] args) {
        List<List<Integer>> got = subsets(new int[]{1, 2, 3});
        // Just check the size and one example
        assert got.size() == 8;
        assert got.contains(List.of(1, 2, 3));
        assert got.contains(List.of());
        System.out.println("all tests passed");
    }
}
```

## Part C — *Permutations* in Python

```python
def permute(nums):
    out = []
    def backtrack(path, used):
        # your code
        ...
    backtrack([], [False] * len(nums))
    return out


if __name__ == "__main__":
    assert len(permute([1, 2, 3])) == 6
    assert sorted(permute([0, 1])) == [[0, 1], [1, 0]]
    print("all tests passed")
```

**Walk-through:**

```python
def permute(nums):
    out = []
    n = len(nums)
    used = [False] * n
    def backtrack(path):
        if len(path) == n:
            out.append(path.copy())
            return
        for i in range(n):
            if used[i]: continue
            used[i] = True
            path.append(nums[i])
            backtrack(path)
            path.pop()
            used[i] = False
    backtrack([])
    return out
```

## Part D — *Permutations* in Java 21

```java
public static List<List<Integer>> permute(int[] nums) {
    List<List<Integer>> out = new ArrayList<>();
    backtrack(out, nums, new ArrayList<>(), new boolean[nums.length]);
    return out;
}

private static void backtrack(List<List<Integer>> out, int[] nums, List<Integer> path, boolean[] used) {
    if (path.size() == nums.length) { out.add(new ArrayList<>(path)); return; }
    for (int i = 0; i < nums.length; i++) {
        if (used[i]) continue;
        used[i] = true;
        path.add(nums[i]);
        backtrack(out, nums, path, used);
        path.remove(path.size() - 1);
        used[i] = false;
    }
}
```

## What you learned

- **Include/skip** for subsets (2^n leaves).
- **Try each unused** for permutations (n! leaves).
- **Path.copy()** when recording so we don't get aliased references.
- **Undo your choice** before returning from the recursive call.

➡️ **[challenge.md](./challenge.md)**
