"""Module 03 — Sliding Window problem catalog."""

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


# 1. Best Time to Buy and Sell Stock (Easy)
add(
    "01-best-time-to-buy-and-sell-stock", "Best Time to Buy and Sell Stock",
    "Easy",
    "You are given an array `prices` where `prices[i]` is the price of a "
    "given stock on the ith day. You want to maximize your profit by "
    "choosing a single day to buy and a different day in the future to "
    "sell. Return the maximum profit. If no profit is possible, return 0.",
    [
        ("prices = [7,1,5,3,6,4]", "5"),  # buy day 1, sell day 4
        ("prices = [7,6,4,3,1]", "0"),
    ],
    [
        "1 <= len(prices) <= 10^5",
        "0 <= prices[i] <= 10^4",
    ],
    [
        "Track the minimum price seen so far.",
        "At each price, the best sell-today profit is `prices[i] - min_so_far`.",
    ],
    "def max_profit(prices: list[int]) -> int:",
    """    min_price = float('inf')
    best = 0
    for p in prices:
        if p < min_price:
            min_price = p
        else:
            best = max(best, p - min_price)
    return best""",
    [
        (([7, 1, 5, 3, 6, 4],), 5),
        (([7, 6, 4, 3, 1],), 0),
        (([2, 4, 1],), 2),
        (([1],), 0),
    ],
    "public static int maxProfit(int[] prices)",
    """        int minPrice = Integer.MAX_VALUE;
        int best = 0;
        for (int p : prices) {
            if (p < minPrice) minPrice = p;
            else best = Math.max(best, p - minPrice);
        }
        return best""",
    [
        ("new int[]{7,1,5,3,6,4}", "5"),
        ("new int[]{7,6,4,3,1}", "0"),
    ],
    """Track the minimum price seen so far. The maximum profit ending at day
`i` is `prices[i] - min(prices[0..i])`. One pass, O(n) time, O(1) space.
""",
)

# 2. Longest Substring Without Repeating Characters (Medium)
add(
    "02-longest-substring-without-repeating-characters",
    "Longest Substring Without Repeating Characters", "Medium",
    "Given a string `s`, find the length of the longest substring without "
    "repeating characters.",
    [
        ("s = 'abcabcbb'", "3"),  # "abc"
        ("s = 'bbbbb'", "1"),
        ("s = 'pwwkew'", "3"),  # "wke"
    ],
    [
        "0 <= len(s) <= 5 * 10^4",
        "s consists of English letters, digits, symbols, and spaces",
    ],
    [
        "Sliding window: maintain `[l, r)` with no repeats.",
        "Use a `set` / `int[128]` to track which chars are in the window. "
        "When `s[r]` is already in the set, advance `l` until it isn't.",
    ],
    "def length_of_longest_substring(s: str) -> int:",
    """    seen: set[str] = set()
    l = 0
    best = 0
    for r, c in enumerate(s):
        while c in seen:
            seen.remove(s[l])
            l += 1
        seen.add(c)
        best = max(best, r - l + 1)
    return best""",
    [
        (("abcabcbb",), 3),
        (("bbbbb",), 1),
        (("pwwkew",), 3),
        (("",), 0),
        ((" ",), 1),
    ],
    "public static int lengthOfLongestSubstring(String s)",
    """        int[] last = new int[128];
        Arrays.fill(last, -1);
        int best = 0;
        for (int r = 0, l = 0; r < s.length(); r++) {
            char c = s.charAt(r);
            if (last[c] >= l) l = last[c] + 1;
            last[c] = r;
            best = Math.max(best, r - l + 1);
        }
        return best""",
    [
        ("\"abcabcbb\"", "3"),
        ("\"bbbbb\"", "1"),
        ("\"pwwkew\"", "3"),
        ("\"\"", "0"),
    ],
    """Sliding window. Two implementations:

- **Set-based** (Python): when a repeat is seen, pop from the left until
  the repeat is gone.
- **Index-based** (Java): `last[c]` stores the last index where char `c`
  appeared. Jump `l` past it if `last[c] >= l`.

Both are O(n).
""",
)

# 3. Longest Repeating Character Replacement (Medium)
add(
    "03-longest-repeating-character-replacement",
    "Longest Repeating Character Replacement", "Medium",
    "You are given a string `s` and an integer `k`. You can choose any "
    "character of the string and change it to any other uppercase English "
    "character. You can perform this operation at most `k` times. Return the "
    "length of the longest substring containing the same letter you can get "
    "after performing the above operations.",
    [
        ("s = 'ABAB', k = 2", "4"),
        ("s = 'AABABBA', k = 1", "4"),
    ],
    [
        "1 <= len(s) <= 10^5",
        "0 <= k <= len(s)",
        "s consists of only uppercase English letters",
    ],
    [
        "For a window, the number of replacements needed is "
        "`window_length - max_count_in_window`.",
        "If that exceeds `k`, shrink from the left.",
    ],
    "def character_replacement(s: str, k: int) -> int:",
    """    from collections import Counter
    counts: Counter[str] = Counter()
    l = 0
    best = 0
    max_count = 0
    for r, c in enumerate(s):
        counts[c] += 1
        max_count = max(max_count, counts[c])
        if (r - l + 1) - max_count > k:
            counts[s[l]] -= 1
            l += 1
        best = max(best, r - l + 1)
    return best""",
    [
        (("ABAB", 2), 4),
        (("AABABBA", 1), 4),
        (("AAAA", 0), 4),
    ],
    "public static int characterReplacement(String s, int k)",
    """        int[] counts = new int[26];
        int l = 0, maxCount = 0, best = 0;
        for (int r = 0; r < s.length(); r++) {
            int idx = s.charAt(r) - 'A';
            counts[idx]++;
            maxCount = Math.max(maxCount, counts[idx]);
            while ((r - l + 1) - maxCount > k) {
                counts[s.charAt(l) - 'A']--;
                l++;
            }
            best = Math.max(best, r - l + 1);
        }
        return best""",
    [
        ("\"ABAB\", 2", "4"),
        ("\"AABABBA\", 1", "4"),
    ],
    """For each window, the number of replacements needed is
`window_length - max_count_of_any_char_in_window`. While that exceeds `k`,
shrink from the left. The `max_count` only ever needs to go up (a smaller
window never has a *larger* max count than a super-window, so we don't
recompute on shrink) — that's the O(n) trick.

**Time:** O(n). **Space:** O(1) (26-letter alphabet) / O(k) general.
""",
)

# 4. Permutation in String (Medium)
add(
    "04-permutation-in-string", "Permutation in String", "Medium",
    "Given two strings `s1` and `s2`, return `True` if `s2` contains a "
    "permutation of `s1`. In other words, return `True` if one of `s1`'s "
    "permutations is a substring of `s2`.",
    [
        ("s1 = 'ab', s2 = 'eidbaooo'", "True"),
        ("s1 = 'ab', s2 = 'eidboaoo'", "False"),
    ],
    [
        "1 <= len(s1), len(s2) <= 10^4",
        "Strings consist of lowercase English letters",
    ],
    [
        "Sliding window of size `len(s1)`. Compare character counts.",
        "Two arrays of size 26 — compare in O(26) per slide.",
    ],
    "def check_inclusion(s1: str, s2: str) -> bool:",
    """    if len(s1) > len(s2):
        return False
    need = [0] * 26
    have = [0] * 26
    for c in s1:
        need[ord(c) - ord('a')] += 1
    for i in range(len(s1)):
        have[ord(s2[i]) - ord('a')] += 1
    if need == have:
        return True
    for i in range(len(s1), len(s2)):
        have[ord(s2[i]) - ord('a')] += 1
        have[ord(s2[i - len(s1)]) - ord('a')] -= 1
        if need == have:
            return True
    return False""",
    [
        (("ab", "eidbaooo"), True),
        (("ab", "eidboaoo"), False),
        (("a", "a"), True),
        (("abc", "ccccbbbbaaaa"), False),
    ],
    "public static boolean checkInclusion(String s1, String s2)",
    """        if (s1.length() > s2.length()) return false;
        int[] need = new int[26], have = new int[26];
        for (int i = 0; i < s1.length(); i++) need[s1.charAt(i) - 'a']++;
        for (int i = 0; i < s1.length(); i++) have[s2.charAt(i) - 'a']++;
        if (Arrays.equals(need, have)) return true;
        for (int i = s1.length(); i < s2.length(); i++) {
            have[s2.charAt(i) - 'a']++;
            have[s2.charAt(i - s1.length()) - 'a']--;
            if (Arrays.equals(need, have)) return true;
        }
        return false""",
    [
        ("\"ab\", \"eidbaooo\"", "true"),
        ("\"ab\", \"eidboaoo\"", "false"),
    ],
    """Fixed-size window of length `len(s1)`. Maintain a count of the window's
characters and compare to `s1`'s count. O(n · 26) is fine for ASCII.

**Time:** O(n · 26) = O(n). **Space:** O(1).
""",
)

# 5. Minimum Size Subarray Sum (Medium)
add(
    "05-minimum-size-subarray-sum", "Minimum Size Subarray Sum", "Medium",
    "Given an array of positive integers `nums` and a positive integer "
    "`target`, return the minimal length of a **contiguous** subarray of "
    "which the sum is at least `target`. If no such subarray exists, "
    "return 0.",
    [
        ("target = 7, nums = [2,3,1,2,4,3]", "2"),
        ("target = 4, nums = [1,4,4]", "1"),
        ("target = 11, nums = [1,1,1,1,1,1,1,1]", "0"),
    ],
    [
        "1 <= target <= 10^9",
        "1 <= len(nums) <= 10^5",
        "1 <= nums[i] <= 10^4",
    ],
    [
        "Variable-size sliding window: extend `r`, shrink `l` while sum >= target.",
        "All values are positive, so a window that satisfies the condition "
        "cannot include any element that makes the sum smaller.",
    ],
    "def min_sub_array_len(target: int, nums: list[int]) -> int:",
    """    l = 0
    s = 0
    best = float('inf')
    for r in range(len(nums)):
        s += nums[r]
        while s >= target:
            best = min(best, r - l + 1)
            s -= nums[l]
            l += 1
    return 0 if best == float('inf') else best""",
    [
        ((7, [2, 3, 1, 2, 4, 3]), 2),
        ((4, [1, 4, 4]), 1),
        ((11, [1, 1, 1, 1, 1, 1, 1, 1]), 0),
    ],
    "public static int minSubArrayLen(int target, int[] nums)",
    """        int l = 0, s = 0, best = Integer.MAX_VALUE;
        for (int r = 0; r < nums.length; r++) {
            s += nums[r];
            while (s >= target) {
                best = Math.min(best, r - l + 1);
                s -= nums[l];
                l++;
            }
        }
        return best == Integer.MAX_VALUE ? 0 : best""",
    [
        ("7, new int[]{2,3,1,2,4,3}", "2"),
        ("4, new int[]{1,4,4}", "1"),
        ("11, new int[]{1,1,1,1,1,1,1,1}", "0"),
    ],
    """Variable window. Extend `r`; while the sum is at least `target`,
shrink from the left and update the best length. O(n) because each
element is added and removed at most once.

> *With negative numbers?* Sliding window doesn't apply; you need
> prefix sums + hash map, or a different technique.
""",
)

# 6. Sliding Window Maximum (Hard)
add(
    "06-sliding-window-maximum", "Sliding Window Maximum", "Hard",
    "You are given an array of integers `nums`, and an integer `k`. There "
    "is a sliding window of size `k` which moves from the very left of the "
    "array to the very right. Return the max of each window.",
    [
        ("nums = [1,3,-1,-3,5,3,6,7], k = 3",
         "[3,3,5,5,6,7]"),
        ("nums = [1], k = 1", "[1]"),
    ],
    [
        "1 <= len(nums) <= 10^5",
        "-10^4 <= nums[i] <= 10^4",
        "1 <= k <= len(nums)",
    ],
    [
        "Brute force: max of each window — O(n · k).",
        "Faster: a **deque** storing indices of candidates in decreasing "
        "value order. The front is always the window max.",
    ],
    "def max_sliding_window(nums: list[int], k: int) -> list[int]:",
    """    from collections import deque
    q: deque[int] = deque()   # indices, values decreasing
    out: list[int] = []
    for i, x in enumerate(nums):
        # drop indices whose value <= x (they can never be the max)
        while q and nums[q[-1]] <= x:
            q.pop()
        q.append(i)
        # drop indices that fell out of the window
        if q[0] <= i - k:
            q.popleft()
        # record max once the first full window is in
        if i >= k - 1:
            out.append(nums[q[0]])
    return out""",
    [
        (([1, 3, -1, -3, 5, 3, 6, 7], 3), [3, 3, 5, 5, 6, 7]),
        (([1], 1), [1]),
        (([9, 11], 2), [11]),
    ],
    "public static int[] maxSlidingWindow(int[] nums, int k)",
    """        Deque<Integer> q = new ArrayDeque<>();
        int n = nums.length;
        int[] out = new int[n - k + 1];
        int idx = 0;
        for (int i = 0; i < n; i++) {
            while (!q.isEmpty() && nums[q.peekLast()] <= nums[i]) q.pollLast();
            q.offerLast(i);
            if (q.peekFirst() <= i - k) q.pollFirst();
            if (i >= k - 1) out[idx++] = nums[q.peekFirst()];
        }
        return out""",
    [
        ("new int[]{1,3,-1,-3,5,3,6,7}, 3", "[3, 3, 5, 5, 6, 7]"),
        ("new int[]{1}, 1", "[1]"),
    ],
    """A **monotonic deque** stores indices in decreasing-value order. The
front is always the max of the current window. On each new element:

1. Pop from the back while the back's value is `<=` the new value (those
   indices can never be a max while the new one is in the window).
2. Push the new index.
3. If the front's index fell out of the window, pop it.
4. Once the first full window is in, record `nums[front]`.

**Time:** O(n) — each index is pushed and popped at most once.
**Space:** O(k).
""",
)
