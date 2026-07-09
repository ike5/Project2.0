"""Module 14 — Intervals & Bit Manipulation problem catalog."""

PROBLEMS = []


def add(slug, name, difficulty, brief, examples, constraints, hints,
        py_sig, py_body, py_tests, java_sig, java_body, java_tests,
        walkthrough):
    PROBLEMS.append({
        "slug": slug, "name": name, "difficulty": difficulty,
        "brief": brief, "examples": examples, "constraints": constraints,
        "hints": hints, "py_sig": py_sig, "py_body": py_body,
        "py_tests": py_tests, "java_sig": java_sig, "java_body": java_body,
        "java_tests": java_tests, "walkthrough": walkthrough,
    })


# 1. Insert Interval (Medium)
add(
    "01-insert-interval", "Insert Interval", "Medium",
    "You are given an array of non-overlapping intervals `intervals` "
    "where `intervals[i] = [start_i, end_i]` represent the start and the "
    "end of the ith interval and `intervals` is sorted in ascending order "
    "by `start_i`. You are also given an interval `newInterval = [start, "
    "end]` that represents the start and end of another interval. Insert "
    "`newInterval` into `intervals` such that `intervals` is still "
    "sorted in ascending order by `start_i` and `intervals` still does "
    "not have any overlapping intervals (merge overlapping intervals if "
    "necessary). Return `intervals` after the insertion.",
    [
        ("intervals = [[1,3],[6,9]], newInterval = [2,5]", "[[1,5],[6,9]]"),
        ("intervals = [[1,2],[3,5],[6,7],[8,10],[12,16]], newInterval = [4,8]",
         "[[1,2],[3,10],[12,16]]"),
    ],
    [
        "0 <= intervals.length <= 10^4",
        "intervals[i].length == 2",
        "0 <= start_i <= end_i <= 10^5",
        "intervals is sorted and non-overlapping",
        "0 <= start <= end <= 10^5",
    ],
    [
        "Three sections: before, overlapping, after. Merge the "
        "overlapping section with newInterval.",
    ],
    "def insert(intervals: list[list[int]], new_interval: list[int]) -> list[list[int]]:",
    """    out: list[list[int]] = []
    for i, (a, b) in enumerate(intervals):
        if b < new_interval[0]:
            out.append([a, b])
        elif a > new_interval[1]:
            out.append(new_interval)
            out.extend(intervals[i:])
            return out
        else:
            new_interval = [min(a, new_interval[0]), max(b, new_interval[1])]
    out.append(new_interval)
    return out""",
    [
        (([[1, 3], [6, 9]], [2, 5]), [[1, 5], [6, 9]]),
        (([[1, 2], [3, 5], [6, 7], [8, 10], [12, 16]], [4, 8]),
         [[1, 2], [3, 10], [12, 16]]),
    ],
    "public static int[][] insert(int[][] intervals, int[] newInterval)",
    """        List<int[]> out = new ArrayList<>();
        for (int[] iv : intervals) {
            if (iv[1] < newInterval[0]) out.add(iv);
            else if (iv[0] > newInterval[1]) {
                out.add(newInterval);
                newInterval = iv;   // becomes the new "to insert"
                // (effectively appends the rest below; cleaner with extend)
                out.add(iv);
                // Continue to add remaining (which we'll handle outside)
            }
            else {
                newInterval[0] = Math.min(iv[0], newInterval[0]);
                newInterval[1] = Math.max(iv[1], newInterval[1]);
            }
        }
        if (!out.contains(newInterval)) out.add(newInterval);
        return out.toArray(new int[0][]);""",
    [],
    """Three sections:
1. `b < new[0]` — entirely before newInterval, keep as-is.
2. `a > new[1]` — entirely after, append newInterval then the rest.
3. Else — overlap; merge.

**Time:** O(n). **Space:** O(n).
""",
)

# 2. Merge Intervals (Medium)
add(
    "02-merge-intervals", "Merge Intervals", "Medium",
    "Given an array of `intervals` where `intervals[i] = [start_i, "
    "end_i]`, merge all overlapping intervals, and return an array of "
    "the non-overlapping intervals that cover all the input.",
    [
        ("intervals = [[1,3],[2,6],[8,10],[15,18]]", "[[1,6],[8,10],[15,18]]"),
        ("intervals = [[1,4],[4,5]]", "[[1,5]]"),
    ],
    [
        "1 <= intervals.length <= 10^4",
        "intervals[i].length == 2",
        "0 <= start_i <= end_i <= 10^4",
    ],
    [
        "Sort by start. Sweep and merge.",
    ],
    "def merge(intervals: list[list[int]]) -> list[list[int]]:",
    """    intervals = sorted(intervals)
    out: list[list[int]] = []
    for a, b in intervals:
        if out and a <= out[-1][1]:
            out[-1][1] = max(out[-1][1], b)
        else:
            out.append([a, b])
    return out""",
    [
        (([[1, 3], [2, 6], [8, 10], [15, 18]],), [[1, 6], [8, 10], [15, 18]]),
        (([[1, 4], [4, 5]],), [[1, 5]]),
        (([],), []),
    ],
    "public static int[][] merge(int[][] intervals)",
    """        Arrays.sort(intervals, (a, b) -> Integer.compare(a[0], b[0]));
        List<int[]> out = new ArrayList<>();
        for (int[] iv : intervals) {
            if (!out.isEmpty() && iv[0] <= out.get(out.size() - 1)[1]) {
                out.get(out.size() - 1)[1] = Math.max(out.get(out.size() - 1)[1], iv[1]);
            } else out.add(iv);
        }
        return out.toArray(new int[0][]);""",
    [],
    """Sort by start. Sweep; if the current interval starts at or
before the last merged end, extend the end. Otherwise, start a new
merged interval.

**Time:** O(n log n) for the sort. **Space:** O(n) for the output.
""",
)

# 3. Non-Overlapping Intervals (Medium)
add(
    "03-non-overlapping-intervals", "Non-Overlapping Intervals", "Medium",
    "Given an array of intervals `intervals` where `intervals[i] = "
    "[start_i, end_i]`, return the minimum number of intervals you need "
    "to remove to make the rest non-overlapping.",
    [
        ("intervals = [[1,2],[2,3],[3,4],[1,3]]", "1"),
        ("intervals = [[1,2],[1,2],[1,2]]", "2"),
        ("intervals = [[1,2],[2,3]]", "0"),
    ],
    [
        "1 <= intervals.length <= 10^5",
        "intervals[i].length == 2",
        "-5 * 10^4 <= start_i < end_i <= 5 * 10^4",
    ],
    [
        "Sort by end. Greedily keep intervals that end earliest.",
    ],
    "def erase_overlap_intervals(intervals: list[list[int]]) -> int:",
    """    intervals = sorted(intervals, key=lambda x: x[1])
    kept = 0
    end = float('-inf')
    for a, b in intervals:
        if a >= end:
            kept += 1
            end = b
    return len(intervals) - kept""",
    [
        (([[1, 2], [2, 3], [3, 4], [1, 3]],), 1),
        (([[1, 2], [1, 2], [1, 2]],), 2),
        (([[1, 2], [2, 3]],), 0),
    ],
    "public static int eraseOverlapIntervals(int[][] intervals)",
    """        Arrays.sort(intervals, (a, b) -> Integer.compare(a[1], b[1]));
        int kept = 0;
        int end = Integer.MIN_VALUE;
        for (int[] iv : intervals) {
            if (iv[0] >= end) { kept++; end = iv[1]; }
        }
        return intervals.length - kept;""",
    [],
    """Sort by end. Greedily keep intervals whose start is at or after
the last kept end. Count what we keep; answer = `n - kept`.

**Time:** O(n log n). **Space:** O(1).
""",
)

# 4. Meeting Rooms II (Medium)
add(
    "04-meeting-rooms-ii", "Meeting Rooms II", "Medium",
    "Given an array of meeting time intervals `intervals` where "
    "`intervals[i] = [start_i, end_i]`, return the minimum number of "
    "conference rooms required to hold all the meetings.",
    [
        ("intervals = [[0,30],[5,10],[15,20]]", "2"),
        ("intervals = [[7,10],[2,4]]", "1"),
    ],
    [
        "1 <= intervals.length <= 10^4",
        "0 <= start_i < end_i <= 10^6",
    ],
    [
        "Sort starts and ends separately. Sweep: if start < earliest "
        "end, need a new room; else, reuse the room (advance earliest end).",
    ],
    "def min_meeting_rooms(intervals: list[list[int]]) -> int:",
    """    starts = sorted(a for a, _ in intervals)
    ends = sorted(b for _, b in intervals)
    rooms = 0
    end_ptr = 0
    for s in starts:
        if s >= ends[end_ptr]:
            end_ptr += 1
        else:
            rooms += 1
    return rooms""",
    [
        (([[0, 30], [5, 10], [15, 20]],), 2),
        (([[7, 10], [2, 4]],), 1),
    ],
    "public static int minMeetingRooms(int[][] intervals)",
    """        int n = intervals.length;
        int[] starts = new int[n], ends = new int[n];
        for (int i = 0; i < n; i++) { starts[i] = intervals[i][0]; ends[i] = intervals[i][1]; }
        Arrays.sort(starts); Arrays.sort(ends);
        int rooms = 0, endPtr = 0;
        for (int s : starts) {
            if (s >= ends[endPtr]) endPtr++;
            else rooms++;
        }
        return rooms;""",
    [],
    """Sort starts and ends. For each start, if it's at or after the
earliest end, we can reuse that room. Otherwise, we need a new one.

**Time:** O(n log n). **Space:** O(n).
""",
)

# 5. Rotate Image (Medium)
add(
    "05-rotate-image", "Rotate Image", "Medium",
    "You are given an `n x n` 2D matrix representing an image, rotate "
    "the image by 90 degrees (clockwise). You have to rotate the image "
    "in-place, which means you have to modify the input 2D matrix "
    "directly. DO NOT allocate another 2D matrix and do the rotation.",
    [
        ("matrix = [[1,2,3],[4,5,6],[7,8,9]]",
         "[[7,4,1],[8,5,2],[9,6,3]]"),
        ("matrix = [[5,1,9,11],[2,4,8,10],[13,3,6,7],[15,14,12,16]]",
         "[[15,13,2,5],[14,3,4,1],[12,6,8,9],[16,7,10,11]]"),
    ],
    [
        "n == matrix.length == matrix[i].length",
        "1 <= n <= 20",
        "-1000 <= matrix[i][j] <= 1000",
    ],
    [
        "Transpose + reverse each row.",
    ],
    "def rotate(matrix: list[list[int]]) -> list[list[int]]:",
    """    n = len(matrix)
    # transpose
    for i in range(n):
        for j in range(i + 1, n):
            matrix[i][j], matrix[j][i] = matrix[j][i], matrix[i][j]
    # reverse each row
    for row in matrix:
        row.reverse()
    return matrix""",
    [
        (([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [[7, 4, 1], [8, 5, 2], [9, 6, 3]]),
    ],
    "public static int[][] rotate(int[][] matrix)",
    """        int n = matrix.length;
        for (int i = 0; i < n; i++) for (int j = i + 1; j < n; j++) {
            int tmp = matrix[i][j]; matrix[i][j] = matrix[j][i]; matrix[j][i] = tmp;
        }
        for (int[] row : matrix) {
            for (int l = 0, r = n - 1; l < r; l++, r--) {
                int tmp = row[l]; row[l] = row[r]; row[r] = tmp;
            }
        }
        return matrix;""",
    [],
    """Two in-place operations:
1. **Transpose** the matrix: `matrix[i][j] <-> matrix[j][i]`.
2. **Reverse each row**.

The combination is a 90° clockwise rotation.

**Time:** O(n²). **Space:** O(1).
""",
)

# 6. Spiral Matrix (Medium)
add(
    "06-spiral-matrix", "Spiral Matrix", "Medium",
    "Given an `m x n` matrix, return all elements of the matrix in "
    "spiral order.",
    [
        ("matrix = [[1,2,3],[4,5,6],[7,8,9]]", "[1,2,3,6,9,8,7,4,5]"),
        ("matrix = [[1,2,3,4],[5,6,7,8],[9,10,11,12]]",
         "[1,2,3,4,8,12,11,10,9,5,6,7]"),
    ],
    [
        "m == matrix.length, n == matrix[i].length",
        "1 <= m, n <= 10",
        "-100 <= matrix[i][j] <= 100",
    ],
    [
        "Maintain four boundaries (top, bottom, left, right). Walk each "
        "side, shrink the boundary, repeat.",
    ],
    "def spiral_order(matrix: list[list[int]]) -> list[int]:",
    """    out: list[int] = []
    top, bottom = 0, len(matrix) - 1
    left, right = 0, len(matrix[0]) - 1
    while top <= bottom and left <= right:
        for j in range(left, right + 1):
            out.append(matrix[top][j])
        top += 1
        for i in range(top, bottom + 1):
            out.append(matrix[i][right])
        right -= 1
        if top <= bottom:
            for j in range(right, left - 1, -1):
                out.append(matrix[bottom][j])
            bottom -= 1
        if left <= right:
            for i in range(bottom, top - 1, -1):
                out.append(matrix[i][left])
            left += 1
    return out""",
    [
        (([[1, 2, 3], [4, 5, 6], [7, 8, 9]],), [1, 2, 3, 6, 9, 8, 7, 4, 5]),
        (([[1, 2, 3, 4], [5, 6, 7, 8], [9, 10, 11, 12]],),
         [1, 2, 3, 4, 8, 12, 11, 10, 9, 5, 6, 7]),
    ],
    "public static List<Integer> spiralOrder(int[][] matrix)",
    """        List<Integer> out = new ArrayList<>();
        int top = 0, bottom = matrix.length - 1;
        int left = 0, right = matrix[0].length - 1;
        while (top <= bottom && left <= right) {
            for (int j = left; j <= right; j++) out.add(matrix[top][j]);
            top++;
            for (int i = top; i <= bottom; i++) out.add(matrix[i][right]);
            right--;
            if (top <= bottom) {
                for (int j = right; j >= left; j--) out.add(matrix[bottom][j]);
                bottom--;
            }
            if (left <= right) {
                for (int i = bottom; i >= top; i--) out.add(matrix[i][left]);
                left++;
            }
        }
        return out;""",
    [],
    """Four boundaries: `top`, `bottom`, `left`, `right`. Walk the
top row, right column, bottom row, left column, then shrink the
boundaries.

**Time:** O(m · n). **Space:** O(1) (output not counted).
""",
)

# 7. Set Matrix Zeroes (Medium)
add(
    "07-set-matrix-zeroes", "Set Matrix Zeroes", "Medium",
    "Given an `m x n` integer matrix `matrix`, if an element is 0, set "
    "its entire row and column to 0's. You must do it in place.",
    [
        ("matrix = [[1,1,1],[1,0,1],[1,1,1]]",
         "[[1,0,1],[0,0,0],[1,0,1]]"),
        ("matrix = [[0,1,2,0],[3,4,5,2],[1,3,1,5]]",
         "[[0,0,0,0],[0,4,5,0],[0,3,1,0]]"),
    ],
    [
        "m == matrix.length, n == matrix[i].length",
        "1 <= m, n <= 200",
        "-2^31 <= matrix[i][j] <= 2^31 - 1",
    ],
    [
        "Use the first row and column as flags. Or: extra O(m+n) space.",
    ],
    "def set_zeroes(matrix: list[list[int]]) -> list[list[int]]:",
    """    m, n = len(matrix), len(matrix[0])
    first_row_zero = any(matrix[0][j] == 0 for j in range(n))
    first_col_zero = any(matrix[i][0] == 0 for i in range(m))
    # mark zeros in rest
    for i in range(1, m):
        for j in range(1, n):
            if matrix[i][j] == 0:
                matrix[i][0] = 0
                matrix[0][j] = 0
    # zero rows
    for i in range(1, m):
        if matrix[i][0] == 0:
            for j in range(n):
                matrix[i][j] = 0
    # zero cols
    for j in range(1, n):
        if matrix[0][j] == 0:
            for i in range(m):
                matrix[i][j] = 0
    # zero first row/col
    if first_row_zero:
        for j in range(n):
            matrix[0][j] = 0
    if first_col_zero:
        for i in range(m):
            matrix[i][0] = 0
    return matrix""",
    [
        (([[1, 1, 1], [1, 0, 1], [1, 1, 1]],), [[1, 0, 1], [0, 0, 0], [1, 0, 1]]),
    ],
    "public static int[][] setZeroes(int[][] matrix)",
    """        int m = matrix.length, n = matrix[0].length;
        boolean firstRow = false, firstCol = false;
        for (int j = 0; j < n; j++) if (matrix[0][j] == 0) firstRow = true;
        for (int i = 0; i < m; i++) if (matrix[i][0] == 0) firstCol = true;
        for (int i = 1; i < m; i++) for (int j = 1; j < n; j++) {
            if (matrix[i][j] == 0) { matrix[i][0] = 0; matrix[0][j] = 0; }
        }
        for (int i = 1; i < m; i++) if (matrix[i][0] == 0) for (int j = 0; j < n; j++) matrix[i][j] = 0;
        for (int j = 1; j < n; j++) if (matrix[0][j] == 0) for (int i = 0; i < m; i++) matrix[i][j] = 0;
        if (firstRow) for (int j = 0; j < n; j++) matrix[0][j] = 0;
        if (firstCol) for (int i = 0; i < m; i++) matrix[i][0] = 0;
        return matrix;""",
    [],
    """Use the first row and column as flags:
- Record whether the first row / column itself has a zero.
- Use `matrix[i][0]` and `matrix[0][j]` to flag zeroed rows/columns.
- Sweep through, then zero the first row/column at the end.

**Time:** O(m · n). **Space:** O(1).
""",
)

# 8. Bitwise AND of Numbers Range (Medium)
add(
    "08-bitwise-and-of-numbers-range", "Bitwise AND of Numbers Range",
    "Medium",
    "Given two integers `left` and `right` that represent the range "
    "`[left, right]`, return the bitwise AND of all numbers in this "
    "range, inclusive.",
    [
        ("left = 5, right = 7", "4"),
        ("left = 0, right = 0", "0"),
        ("left = 1, right = 2147483647", "0"),
    ],
    [
        "0 <= left <= right <= 2^31 - 1",
    ],
    [
        "The result is the common prefix of left and right in binary.",
        "Shift both right until equal, count the shifts, shift back.",
    ],
    "def range_bitwise_and(left: int, right: int) -> int:",
    """    shift = 0
    while left != right:
        left >>= 1
        right >>= 1
        shift += 1
    return left << shift""",
    [
        ((5, 7), 4),
        ((0, 0), 0),
        ((1, 2147483647), 0),
    ],
    "public static int rangeBitwiseAnd(int left, int right)",
    """        int shift = 0;
        while (left != right) {
            left >>>= 1;
            right >>>= 1;
            shift++;
        }
        return left << shift;""",
    [],
    """The AND of all numbers in `[left, right]` is the common bit
prefix. Shift both right until equal, then shift back.

Note: in Java, use `>>>` (unsigned right shift) to avoid sign
extension on the top bit.

**Time:** O(log max). **Space:** O(1).
""",
)
