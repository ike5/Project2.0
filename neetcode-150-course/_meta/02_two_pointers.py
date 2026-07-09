"""Module 02 — Two Pointers problem catalog."""

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


# 1. Valid Palindrome (Easy)
add(
    "01-valid-palindrome", "Valid Palindrome", "Easy",
    "Given a string `s`, return `True` if it is a palindrome after "
    "converting all uppercase letters to lowercase and removing all "
    "non-alphanumeric characters.",
    [
        ("s = 'A man, a plan, a canal: Panama'", "True"),
        ("s = 'race a car'", "False"),
        ("s = ' '", "True"),
    ],
    [
        "1 <= len(s) <= 2 * 10^5",
        "s consists of printable ASCII characters",
    ],
    [
        "Two pointers from opposite ends.",
        "Skip non-alphanumeric chars and compare lowercased values.",
    ],
    "def is_palindrome(s: str) -> bool:",
    """    l, r = 0, len(s) - 1
    while l < r:
        while l < r and not s[l].isalnum():
            l += 1
        while l < r and not s[r].isalnum():
            r -= 1
        if s[l].lower() != s[r].lower():
            return False
        l += 1
        r -= 1
    return True""",
    [
        (("A man, a plan, a canal: Panama",), True),
        (("race a car",), False),
        ((" ",), True),
        (("a",), True),
        (("ab",), False),
    ],
    "public static boolean isPalindrome(String s)",
    """        int l = 0, r = s.length() - 1;
        while (l < r) {
            while (l < r && !Character.isLetterOrDigit(s.charAt(l))) l++;
            while (l < r && !Character.isLetterOrDigit(s.charAt(r))) r--;
            if (Character.toLowerCase(s.charAt(l)) != Character.toLowerCase(s.charAt(r))) {
                return false;
            }
            l++;
            r--;
        }
        return true""",
    [
        ("\"A man, a plan, a canal: Panama\"", "true"),
        ("\"race a car\"", "false"),
        ("\" \"", "true"),
        ("\"a\"", "true"),
    ],
    """Two pointers from opposite ends. Skip non-alphanumeric characters at
each step. Compare the lowercased chars. If they ever differ, the string is
not a palindrome.

**Time:** O(n). **Space:** O(1) — pointers only.
""",
)

# 2. Two Sum II - Input Array Is Sorted (Easy)
add(
    "02-two-sum-ii-input-array-is-sorted", "Two Sum II — Input Array Is Sorted",
    "Easy",
    "Given a **1-indexed** array of integers `numbers` that is already "
    "sorted in non-decreasing order, find two numbers such that they add up "
    "to a specific `target`. Return the indices of the two numbers as a "
    "1-indexed array `[i, j]`. You may not use the same element twice.",
    [
        ("numbers = [2,7,11,15], target = 9", "[1, 2]"),
        ("numbers = [2,3,4],     target = 6", "[1, 3]"),
        ("numbers = [-1,0],      target = -1", "[1, 2]"),
    ],
    [
        "2 <= len(numbers) <= 3 * 10^4",
        "-1000 <= numbers[i] <= 1000",
        "numbers is sorted in non-decreasing order",
        "Exactly one valid answer",
    ],
    [
        "Sorted input → two pointers from opposite ends.",
        "If sum too small, advance `l`; if too large, retreat `r`.",
    ],
    "def two_sum_sorted(numbers: list[int], target: int) -> list[int]:",
    """    l, r = 0, len(numbers) - 1
    while l < r:
        s = numbers[l] + numbers[r]
        if s == target:
            return [l + 1, r + 1]   # 1-indexed
        if s < target:
            l += 1
        else:
            r -= 1
    return []""",
    [
        (([2, 7, 11, 15], 9), [1, 2]),
        (([2, 3, 4], 6), [1, 3]),
        (([-1, 0], -1), [1, 2]),
    ],
    "public static int[] twoSumSorted(int[] numbers, int target)",
    """        int l = 0, r = numbers.length - 1;
        while (l < r) {
            int s = numbers[l] + numbers[r];
            if (s == target) return new int[] { l + 1, r + 1 };
            if (s < target) l++;
            else r--;
        }
        return new int[] {}""",
    [
        ("new int[]{2,7,11,15}, 9", "[1, 2]"),
        ("new int[]{2,3,4}, 6", "[1, 3]"),
        ("new int[]{-1,0}, -1", "[1, 2]"),
    ],
    """Two pointers from opposite ends. The array is sorted, so adjusting one
pointer monotonically moves the sum in the right direction.

**Time:** O(n). **Space:** O(1).
""",
)

# 3. 3Sum (Medium)
add(
    "03-three-sum", "3Sum", "Medium",
    "Given an integer array `nums`, return all the triplets "
    "`[nums[i], nums[j], nums[k]]` such that `i != j`, `i != k`, and "
    "`j != k`, and `nums[i] + nums[j] + nums[k] == 0`. The solution set "
    "must not contain duplicate triplets.",
    [
        ("nums = [-1,0,1,2,-1,-4]", "[[-1,-1,2],[-1,0,1]]"),
        ("nums = [0,1,1]", "[]"),
        ("nums = [0,0,0]", "[[0,0,0]]"),
    ],
    [
        "3 <= len(nums) <= 3000",
        "-10^5 <= nums[i] <= 10^5",
    ],
    [
        "Sort first. Then for each i, run a two-pointer search on the rest.",
        "Skip duplicates at i, l, and r to avoid emitting the same triplet "
        "twice.",
    ],
    "def three_sum(nums: list[int]) -> list[list[int]]:",
    """    nums = sorted(nums)
    n = len(nums)
    out: list[list[int]] = []
    for i in range(n - 2):
        if i > 0 and nums[i] == nums[i - 1]:
            continue
        l, r = i + 1, n - 1
        while l < r:
            s = nums[i] + nums[l] + nums[r]
            if s == 0:
                out.append([nums[i], nums[l], nums[r]])
                while l < r and nums[l] == nums[l + 1]:
                    l += 1
                while l < r and nums[r] == nums[r - 1]:
                    r -= 1
                l += 1
                r -= 1
            elif s < 0:
                l += 1
            else:
                r -= 1
    return out""",
    [
        (([-1, 0, 1, 2, -1, -4],),
         [[-1, -1, 2], [-1, 0, 1]]),
        (([0, 1, 1],), []),
        (([0, 0, 0],), [[0, 0, 0]]),
    ],
    "public static List<List<Integer>> threeSum(int[] nums)",
    """        Arrays.sort(nums);
        int n = nums.length;
        List<List<Integer>> out = new ArrayList<>();
        for (int i = 0; i < n - 2; i++) {
            if (i > 0 && nums[i] == nums[i - 1]) continue;
            int l = i + 1, r = n - 1;
            while (l < r) {
                int s = nums[i] + nums[l] + nums[r];
                if (s == 0) {
                    out.add(Arrays.asList(nums[i], nums[l], nums[r]));
                    while (l < r && nums[l] == nums[l + 1]) l++;
                    while (l < r && nums[r] == nums[r - 1]) r--;
                    l++;
                    r--;
                } else if (s < 0) {
                    l++;
                } else {
                    r--;
                }
            }
        }
        return out""",
    [],
    """Sort, then fix `i` and run a two-pointer search on the rest. Skip
duplicates at every level.

**Time:** O(n²) — O(n log n) to sort, O(n²) for the nested loops (each pair
of `l, r` moves at most n times). **Space:** O(1) extra (output not counted).
""",
)

# 4. Container With Most Water (Medium)
add(
    "04-container-with-most-water", "Container With Most Water", "Medium",
    "Given `n` non-negative integers `height` where each represents a point "
    "at coordinate `(i, height[i])`, find two lines that together with the "
    "x-axis form a container that holds the most water.",
    [
        ("height = [1,8,6,2,5,4,8,3,7]", "49"),
        ("height = [1,1]", "1"),
    ],
    [
        "2 <= n <= 10^5",
        "0 <= height[i] <= 10^4",
    ],
    [
        "Brute force tries every pair: O(n²). Two pointers does it in O(n).",
        "Start with the widest container; only move the *shorter* line in, "
        "because moving the taller one can never increase the area.",
    ],
    "def max_area(height: list[int]) -> int:",
    """    l, r = 0, len(height) - 1
    best = 0
    while l < r:
        area = (r - l) * min(height[l], height[r])
        best = max(best, area)
        if height[l] < height[r]:
            l += 1
        else:
            r -= 1
    return best""",
    [
        (([1, 8, 6, 2, 5, 4, 8, 3, 7],), 49),
        (([1, 1],), 1),
        (([4, 3, 2, 1, 4],), 16),
    ],
    "public static int maxArea(int[] height)",
    """        int l = 0, r = height.length - 1;
        int best = 0;
        while (l < r) {
            int area = (r - l) * Math.min(height[l], height[r]);
            best = Math.max(best, area);
            if (height[l] < height[r]) l++;
            else r--;
        }
        return best""",
    [
        ("new int[]{1,8,6,2,5,4,8,3,7}", "49"),
        ("new int[]{1,1}", "1"),
        ("new int[]{4,3,2,1,4}", "16"),
    ],
    """Greedy two pointers. Start widest; move the shorter side inward (moving
the taller one cannot increase the area at any later step).

**Time:** O(n). **Space:** O(1).
""",
)

# 5. Trapping Rain Water (Hard)
add(
    "05-trapping-rain-water", "Trapping Rain Water", "Hard",
    "Given `n` non-negative integers representing an elevation map where the "
    "width of each bar is 1, compute how much water it can trap after "
    "raining.",
    [
        ("height = [0,1,0,2,1,0,1,3,2,1,2,1]", "6"),
        ("height = [4,2,0,3,2,5]", "9"),
    ],
    [
        "n == len(height)",
        "1 <= n <= 2 * 10^4",
        "0 <= height[i] <= 10^5",
    ],
    [
        "Water at index i = min(max_left, max_right) - height[i].",
        "Two-pointer version: keep `l_max` and `r_max`, advance the side "
        "with the smaller running max.",
        "Alternative: a stack of decreasing heights (Module 04).",
    ],
    "def trap(height: list[int]) -> int:",
    """    l, r = 0, len(height) - 1
    l_max = r_max = 0
    water = 0
    while l < r:
        if height[l] < height[r]:
            if height[l] >= l_max:
                l_max = height[l]
            else:
                water += l_max - height[l]
            l += 1
        else:
            if height[r] >= r_max:
                r_max = height[r]
            else:
                water += r_max - height[r]
            r -= 1
    return water""",
    [
        (([0, 1, 0, 2, 1, 0, 1, 3, 2, 1, 2, 1],), 6),
        (([4, 2, 0, 3, 2, 5],), 9),
        (([1, 0, 1],), 1),
    ],
    "public static int trap(int[] height)",
    """        int l = 0, r = height.length - 1;
        int lMax = 0, rMax = 0, water = 0;
        while (l < r) {
            if (height[l] < height[r]) {
                if (height[l] >= lMax) lMax = height[l];
                else water += lMax - height[l];
                l++;
            } else {
                if (height[r] >= rMax) rMax = height[r];
                else water += rMax - height[r];
                r--;
            }
        }
        return water""",
    [
        ("new int[]{0,1,0,2,1,0,1,3,2,1,2,1}", "6"),
        ("new int[]{4,2,0,3,2,5}", "9"),
        ("new int[]{1,0,1}", "1"),
    ],
    """Water at index i is `min(max_left, max_right) - height[i]`. We don't
need to precompute the max arrays: a two-pointer pass with `lMax` and `rMax`
does the same job in O(1) extra space.

**Time:** O(n). **Space:** O(1).
""",
)
