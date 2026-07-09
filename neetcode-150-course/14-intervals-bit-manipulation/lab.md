# Lab 14 — Intervals & Bit Manipulation

**You'll:** implement *Merge Intervals* and *Rotate Image* in both
languages. ⏱️ ~1 h.

---

## Part A — *Merge Intervals* in Python

```python
def merge(intervals):
    intervals = sorted(intervals)
    out = []
    for a, b in intervals:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out


if __name__ == "__main__":
    assert merge([[1, 3], [2, 6], [8, 10], [15, 18]]) == [[1, 6], [8, 10], [15, 18]]
    assert merge([[1, 4], [4, 5]]) == [[1, 5]]
    assert merge([]) == []
    print("all tests passed")
```

`if out and a <= out[-1][1]` checks if the current interval overlaps
with the last merged one. Note that `<=` is correct because two
intervals that touch at a single point (e.g. `[1, 4]` and `[4, 5]`)
should merge.

## Part B — *Merge Intervals* in Java 21

```java
import java.util.*;

public class LabMerge {
    public static int[][] merge(int[][] intervals) {
        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        List<int[]> out = new ArrayList<>();
        for (int[] iv : intervals) {
            if (!out.isEmpty() && iv[0] <= out.get(out.size() - 1)[1]) {
                out.get(out.size() - 1)[1] = Math.max(out.get(out.size() - 1)[1], iv[1]);
            } else out.add(iv);
        }
        return out.toArray(new int[0][]);
    }

    public static void main(String[] args) {
        int[][] a = {{1, 3}, {2, 6}, {8, 10}, {15, 18}};
        int[][] got = merge(a);
        assert got.length == 3;
        assert got[0][0] == 1 && got[0][1] == 6;
        assert got[1][0] == 8 && got[1][1] == 10;
        assert got[2][0] == 15 && got[2][1] == 18;
        System.out.println("all tests passed");
    }
}
```

## Part C — *Rotate Image* in Python

```python
def rotate(matrix):
    n = len(matrix)
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    for row in matrix:
        row.reverse()
    return matrix


if __name__ == "__main__":
    m = [[1, 2, 3], [4, 5, 6], [7, 8, 9]]
    assert rotate(m) == [[7, 4, 1], [8, 5, 2], [9, 6, 3]]
    print("all tests passed")
```

Transpose, then reverse each row.

## Part D — *Rotate Image* in Java 21

```java
public class LabRotate {
    public static int[][] rotate(int[][] matrix) {
        int n = matrix.length;
        for (int i = 0; i < n; i++) {
            for (int j = i + 1; j < n; j++) {
                int tmp = matrix[i][j];
                matrix[i][j] = matrix[j][i];
                matrix[j][i] = tmp;
            }
        }
        for (int[] row : matrix) {
            for (int l = 0, r = n - 1; l < r; l++, r--) {
                int tmp = row[l];
                row[l] = row[r];
                row[r] = tmp;
            }
        }
        return matrix;
    }

    public static void main(String[] args) {
        int[][] m = {{1, 2, 3}, {4, 5, 6}, {7, 8, 9}};
        int[][] got = rotate(m);
        assert got[0][0] == 7 && got[0][1] == 4 && got[0][2] == 1;
        assert got[1][0] == 8 && got[1][1] == 5 && got[1][2] == 2;
        assert got[2][0] == 9 && got[2][1] == 6 && got[2][2] == 3;
        System.out.println("all tests passed");
    }
}
```

## What you learned

- **Sort by start, sweep with a "last merged" pointer.**
- **In-place transpose + row reverse** = 90° clockwise rotation.

➡️ **[challenge.md](./challenge.md)**
