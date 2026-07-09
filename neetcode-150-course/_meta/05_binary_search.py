"""Module 05 — Binary Search problem catalog."""

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


# 1. Binary Search (Easy)
add(
    "01-binary-search", "Binary Search", "Easy",
    "Given a **sorted** array of integers `nums` of length `n` and a "
    "target, return the index of `target` if it is in `nums`, or `-1` if "
    "it is not. You must write an algorithm with O(log n) runtime.",
    [
        ("nums = [-1,0,3,5,9,12], target = 9", "4"),
        ("nums = [-1,0,3,5,9,12], target = 2", "-1"),
    ],
    [
        "1 <= n <= 10^4",
        "-10^4 < nums[i], target < 10^4",
        "All integers in nums are unique",
        "nums is sorted in ascending order",
    ],
    [
        "Classic half-interval search.",
        "Use `lo + (hi - lo) // 2` to avoid overflow in Java `int`.",
    ],
    "def search(nums: list[int], target: int) -> int:",
    """    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[mid] < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1""",
    [
        (([-1, 0, 3, 5, 9, 12], 9), 4),
        (([-1, 0, 3, 5, 9, 12], 2), -1),
        (([5], 5), 0),
        (([1, 2, 3, 4, 5], 6), -1),
    ],
    "public static int search(int[] nums, int target)",
    """        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[mid] < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return -1""",
    [
        ("new int[]{-1,0,3,5,9,12}, 9", "4"),
        ("new int[]{-1,0,3,5,9,12}, 2", "-1"),
    ],
    """The classic. Two things to internalize:

- **Loop guard:** `while lo <= hi`. If `lo > hi`, the target isn't there.
- **Midpoint:** `lo + (hi - lo) // 2` (Java: `/ 2`). Avoids `int` overflow
  in languages where `(lo + hi) / 2` could overflow.
""",
)

# 2. Search a 2D Matrix (Medium)
add(
    "02-search-a-2d-matrix", "Search a 2D Matrix", "Medium",
    "You are given an `m x n` integer matrix `matrix` with the following "
    "two properties: (1) each row is sorted in non-decreasing order; "
    "(2) the first integer of each row is greater than the last integer "
    "of the previous row. Given an integer `target`, return `True` if "
    "`target` is in `matrix`, or `False` otherwise. You must write a "
    "solution in O(log(m*n)) time.",
    [
        ("matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 3", "True"),
        ("matrix = [[1,3,5,7],[10,11,16,20],[23,30,34,60]], target = 13", "False"),
    ],
    [
        "m == matrix.length, n == matrix[i].length",
        "1 <= m, n <= 100",
        "-10^4 <= matrix[i][j], target <= 10^4",
    ],
    [
        "Treat the matrix as a flat sorted array of size m*n.",
        "Index `(i, j)` becomes `i * n + j` in the flat array.",
    ],
    "def search_matrix(matrix: list[list[int]], target: int) -> bool:",
    """    if not matrix or not matrix[0]:
        return False
    m, n = len(matrix), len(matrix[0])
    lo, hi = 0, m * n - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        v = matrix[mid // n][mid % n]
        if v == target:
            return True
        if v < target:
            lo = mid + 1
        else:
            hi = mid - 1
    return False""",
    [
        (([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 3), True),
        (([[1, 3, 5, 7], [10, 11, 16, 20], [23, 30, 34, 60]], 13), False),
    ],
    "public static boolean searchMatrix(int[][] matrix, int target)",
    """        if (matrix.length == 0 || matrix[0].length == 0) return false;
        int m = matrix.length, n = matrix[0].length;
        int lo = 0, hi = m * n - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            int v = matrix[mid / n][mid % n];
            if (v == target) return true;
            if (v < target) lo = mid + 1;
            else hi = mid - 1;
        }
        return false""",
    [],
    """Map a flat index `k` to a 2D index via `(k // n, k % n)`. Then
standard binary search on the flat array.

**Time:** O(log(m*n)). **Space:** O(1).
""",
)

# 3. Koko Eating Bananas (Medium)
add(
    "03-koko-eating-bananas", "Koko Eating Bananas", "Medium",
    "Koko loves to eat bananas. There are `n` piles of bananas, the ith "
    "pile has `piles[i]` bananas. The guards have gone and will come back "
    "in `h` hours. Koko can decide her bananas-per-hour eating speed of "
    "`k`. Each hour, she chooses some pile of bananas and eats `k` "
    "bananas from that pile. If the pile has less than `k` bananas, she "
    "eats all of them and won't eat any more bananas during that hour. "
    "Return the minimum integer `k` such that she can eat all the bananas "
    "within `h` hours.",
    [
        ("piles = [1,4,3,2], h = 9", "2"),
        ("piles = [25,10,23,4], h = 4", "25"),
    ],
    [
        "1 <= piles.length <= 10^4",
        "piles.length <= h <= 10^9",
        "1 <= piles[i] <= 10^9",
    ],
    [
        "Binary search on the answer (k).",
        "If a candidate k is too slow, increase. If fast enough, try "
        "smaller.",
    ],
    "def min_eating_speed(piles: list[int], h: int) -> int:",
    """    lo, hi = 1, max(piles)
    while lo < hi:
        mid = (lo + hi) // 2
        hours = sum((p + mid - 1) // mid for p in piles)   # ceil(p / mid)
        if hours <= h:
            hi = mid
        else:
            lo = mid + 1
    return lo""",
    [
        (([1, 4, 3, 2], 9), 2),
        (([25, 10, 23, 4], 4), 25),
        (([3, 6, 7, 11], 8), 4),
    ],
    "public static int minEatingSpeed(int[] piles, int h)",
    """        int lo = 1, hi = 0;
        for (int p : piles) hi = Math.max(hi, p);
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            int hours = 0;
            for (int p : piles) hours += (p + mid - 1) / mid;
            if (hours <= h) hi = mid;
            else lo = mid + 1;
        }
        return lo""",
    [
        ("new int[]{1,4,3,2}, 9", "2"),
        ("new int[]{25,10,23,4}, 4", "25"),
    ],
    """Binary search on the eating speed. For a candidate `k`, the number
of hours needed is `sum(ceil(p / k) for p in piles)`. The predicate
"can finish in `h` hours" is monotone in `k` (faster → fewer hours), so
we can binary-search.

**Time:** O(n log(max(p))). **Space:** O(1).
""",
)

# 4. Find Minimum In Rotated Sorted Array (Medium)
add(
    "04-find-minimum-in-rotated-sorted-array",
    "Find Minimum in Rotated Sorted Array", "Medium",
    "Suppose an array of length `n` sorted in ascending order is rotated "
    "between 1 and n times. Given the sorted rotated array `nums` of "
    "unique elements, return the minimum element of this array. You must "
    "write an algorithm that runs in O(log n) time.",
    [
        ("nums = [3,4,5,1,2]", "1"),
        ("nums = [4,5,6,7,0,1,2]", "0"),
        ("nums = [11,13,15,17]", "11"),  # not rotated
    ],
    [
        "n == nums.length",
        "1 <= n <= 5000",
        "-5000 <= nums[i] <= 5000",
        "All integers in nums are unique",
        "nums is sorted and rotated between 1 and n times",
    ],
    [
        "Compare `nums[mid]` to `nums[hi]`. If `nums[mid] > nums[hi]`, "
        "the min is in the right half; else in the left.",
    ],
    "def find_min(nums: list[int]) -> int:",
    """    lo, hi = 0, len(nums) - 1
    while lo < hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] > nums[hi]:
            lo = mid + 1
        else:
            hi = mid
    return nums[lo]""",
    [
        (([3, 4, 5, 1, 2],), 1),
        (([4, 5, 6, 7, 0, 1, 2],), 0),
        (([11, 13, 15, 17],), 11),
    ],
    "public static int findMin(int[] nums)",
    """        int lo = 0, hi = nums.length - 1;
        while (lo < hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] > nums[hi]) lo = mid + 1;
            else hi = mid;
        }
        return nums[lo]""",
    [
        ("new int[]{3,4,5,1,2}", "1"),
        ("new int[]{4,5,6,7,0,1,2}", "0"),
    ],
    """Comparing `nums[mid]` to `nums[hi]` (not `nums[lo]`) makes the
analysis cleaner: if `nums[mid] > nums[hi]`, the min is in the right
half (the rotation pivot is to the right of mid); otherwise it's in the
left half (including mid).

**Time:** O(log n). **Space:** O(1).
""",
)

# 5. Search In Rotated Sorted Array (Medium)
add(
    "05-search-in-rotated-sorted-array", "Search in Rotated Sorted Array",
    "Medium",
    "There is an integer array `nums` sorted in ascending order (with "
    "distinct values). Prior to being passed to your function, `nums` is "
    "possibly rotated at an unknown pivot. Given the array `nums` and an "
    "integer `target`, return the index of `target` if it is in `nums`, "
    "or `-1` if it is not. You must write an algorithm with O(log n) "
    "runtime.",
    [
        ("nums = [4,5,6,7,0,1,2], target = 0", "4"),
        ("nums = [4,5,6,7,0,1,2], target = 3", "-1"),
        ("nums = [1], target = 0", "-1"),
    ],
    [
        "1 <= n <= 5000",
        "-10^4 <= nums[i] <= 10^4",
        "All values in nums are unique",
        "nums is an ascending array that is possibly rotated",
    ],
    [
        "At each step, one half is sorted. Check if the target is in the "
        "sorted half; if so, search there; else, search the other half.",
    ],
    "def search_rotated(nums: list[int], target: int) -> int:",
    """    lo, hi = 0, len(nums) - 1
    while lo <= hi:
        mid = lo + (hi - lo) // 2
        if nums[mid] == target:
            return mid
        if nums[lo] <= nums[mid]:                  # left half sorted
            if nums[lo] <= target < nums[mid]:
                hi = mid - 1
            else:
                lo = mid + 1
        else:                                      # right half sorted
            if nums[mid] < target <= nums[hi]:
                lo = mid + 1
            else:
                hi = mid - 1
    return -1""",
    [
        (([4, 5, 6, 7, 0, 1, 2], 0), 4),
        (([4, 5, 6, 7, 0, 1, 2], 3), -1),
        (([1], 0), -1),
        (([3, 1], 1), 1),
    ],
    "public static int searchRotated(int[] nums, int target)",
    """        int lo = 0, hi = nums.length - 1;
        while (lo <= hi) {
            int mid = lo + (hi - lo) / 2;
            if (nums[mid] == target) return mid;
            if (nums[lo] <= nums[mid]) {
                if (nums[lo] <= target && target < nums[mid]) hi = mid - 1;
                else lo = mid + 1;
            } else {
                if (nums[mid] < target && target <= nums[hi]) lo = mid + 1;
                else hi = mid - 1;
            }
        }
        return -1""",
    [
        ("new int[]{4,5,6,7,0,1,2}, 0", "4"),
        ("new int[]{4,5,6,7,0,1,2}, 3", "-1"),
    ],
    """At every step one half is sorted. Decide which half to keep based
on whether the target lies in the sorted range.

**Time:** O(log n). **Space:** O(1).
""",
)

# 6. Time Based Key Value Store (Medium)
add(
    "06-time-based-key-value-store", "Time Based Key-Value Store", "Medium",
    "Design a time-based key-value data structure that can store multiple "
    "values for the same key at different time stamps and retrieve the "
    "key's value at a certain timestamp. Implement the `TimeMap` class "
    "with `set(key, value, timestamp)` and `get(key, timestamp)` methods.",
    [
        ("TimeMap(); set('foo','bar',1); get('foo',1) -> 'bar'; "
         "get('foo',3) -> 'bar' (no value at ts 3, use ts 1)",
         "['bar','bar']"),
    ],
    [
        "1 <= key.length, value.length <= 100",
        "key and value consist of lowercase English letters and digits",
        "1 <= timestamp <= 10^7",
        "set is called at most 2 * 10^5 times per test",
        "get is called at most 2 * 10^5 times per test",
    ],
    [
        "Per key, store a list of (timestamp, value), sorted by timestamp.",
        "`get` is a binary search for the largest timestamp <= the query.",
    ],
    "class TimeMap:",
    """    def __init__(self) -> None:
        self._data: dict[str, list[tuple[int, str]]] = {}

    def set(self, key: str, value: str, timestamp: int) -> None:
        self._data.setdefault(key, []).append((timestamp, value))

    def get(self, key: str, timestamp: int) -> str:
        if key not in self._data:
            return ""
        entries = self._data[key]
        lo, hi = 0, len(entries) - 1
        best = ""
        while lo <= hi:
            mid = (lo + hi) // 2
            if entries[mid][0] <= timestamp:
                best = entries[mid][1]
                lo = mid + 1
            else:
                hi = mid - 1
        return best""",
    [
        (("__init__",), None),
    ],
    "public static class TimeMap",
    """        private final Map<String, List<int[]>> map = new HashMap<>();
        // each int[] is [timestamp, valueHash] — we store String separately
        private final Map<String, List<String>> values = new HashMap<>();

        public void set(String key, String value, int timestamp) {
            map.computeIfAbsent(key, k -> new ArrayList<>()).add(new int[]{timestamp, 0});
            values.computeIfAbsent(key, k -> new ArrayList<>()).add(value);
        }

        public String get(String key, int timestamp) {
            List<int[]> times = map.get(key);
            if (times == null) return "";
            int lo = 0, hi = times.size() - 1;
            String best = "";
            while (lo <= hi) {
                int mid = (lo + hi) / 2;
                if (times.get(mid)[0] <= timestamp) {
                    best = values.get(key).get(mid);
                    lo = mid + 1;
                } else {
                    hi = mid - 1;
                }
            }
            return best;
        }""",
    [],
    """Two maps of lists: one for timestamps, one for values (kept in sync
by index). `get` binary-searches the timestamps for the largest one `<=`
the query, and returns the corresponding value (or `""` if no such
timestamp exists).

**Time:** O(log n) per `get`, O(1) amortized per `set`. **Space:** O(n).
""",
)

# 7. Median Of Two Sorted Arrays (Hard)
add(
    "07-median-of-two-sorted-arrays", "Median of Two Sorted Arrays", "Hard",
    "Given two sorted arrays `nums1` and `nums2` of size `m` and `n` "
    "respectively, return the median of the two sorted arrays. The "
    "overall run time complexity should be O(log (m+n)).",
    [
        ("nums1 = [1,3], nums2 = [2]", "2.0"),
        ("nums1 = [1,2], nums2 = [3,4]", "2.5"),
    ],
    [
        "0 <= m, n <= 1000",
        "1 <= m + n <= 2000",
        "-10^6 <= nums1[i], nums2[i] <= 10^6",
    ],
    [
        "Binary search the smaller array for the partition that "
        "correctly splits the combined sorted array.",
        "Left of partition (combined) has half the elements; right has the other half.",
    ],
    "def find_median_sorted_arrays(nums1: list[int], nums2: list[int]) -> float:",
    """    # ensure nums1 is the smaller
    if len(nums1) > len(nums2):
        nums1, nums2 = nums2, nums1
    m, n = len(nums1), len(nums2)
    lo, hi = 0, m
    while lo <= hi:
        i = (lo + hi) // 2
        j = (m + n + 1) // 2 - i
        left1 = nums1[i - 1] if i > 0 else float('-inf')
        right1 = nums1[i]     if i < m else float('inf')
        left2 = nums2[j - 1] if j > 0 else float('-inf')
        right2 = nums2[j]     if j < n else float('inf')
        if left1 <= right2 and left2 <= right1:
            if (m + n) % 2 == 1:
                return float(max(left1, left2))
            return (max(left1, left2) + min(right1, right2)) / 2.0
        if left1 > right2:
            hi = i - 1
        else:
            lo = i + 1
    return 0.0""",
    [
        (([1, 3], [2]), 2.0),
        (([1, 2], [3, 4]), 2.5),
        (([], [1]), 1.0),
    ],
    "public static double findMedianSortedArrays(int[] nums1, int[] nums2)",
    """        if (nums1.length > nums2.length) { int[] t = nums1; nums1 = nums2; nums2 = t; }
        int m = nums1.length, n = nums2.length;
        int lo = 0, hi = m;
        while (lo <= hi) {
            int i = (lo + hi) / 2;
            int j = (m + n + 1) / 2 - i;
            int left1 = (i == 0) ? Integer.MIN_VALUE : nums1[i - 1];
            int right1 = (i == m) ? Integer.MAX_VALUE : nums1[i];
            int left2 = (j == 0) ? Integer.MIN_VALUE : nums2[j - 1];
            int right2 = (j == n) ? Integer.MAX_VALUE : nums2[j];
            if (left1 <= right2 && left2 <= right1) {
                if (((m + n) & 1) == 1) return Math.max(left1, left2);
                return (Math.max(left1, left2) + Math.min(right1, right2)) / 2.0;
            }
            if (left1 > right2) hi = i - 1;
            else lo = i + 1;
        }
        return 0.0""",
    [
        ("new int[]{1,3}, new int[]{2}", "2.0"),
        ("new int[]{1,2}, new int[]{3,4}", "2.5"),
    ],
    """Binary search the smaller array for the correct partition. A
correct partition has `left1 <= right2` and `left2 <= right1`. The
median is then derived from the four boundary values.

**Time:** O(log(min(m, n))). **Space:** O(1).

This is the canonical "binary search the answer space" problem and
shows up in interviews even when not asked directly — it teaches the
partition technique used in many other search problems.
""",
)
