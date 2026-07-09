"""Module 12 — Dynamic Programming problem catalog.

The biggest module. 22 problems, easy → hard.
"""

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


# 1. Climbing Stairs (Easy)
add(
    "01-climbing-stairs", "Climbing Stairs", "Easy",
    "You are climbing a staircase. It takes `n` steps to reach the top. "
    "Each time you can either climb 1 or 2 steps. In how many distinct "
    "ways can you climb to the top?",
    [
        ("n = 2", "2"),
        ("n = 3", "3"),
    ],
    [
        "1 <= n <= 45",
    ],
    [
        "This is the Fibonacci sequence.",
    ],
    "def climb_stairs(n: int) -> int:",
    """    if n <= 2: return n
    a, b = 1, 2
    for _ in range(3, n + 1):
        a, b = b, a + b
    return b""",
    [
        ((2,), 2),
        ((3,), 3),
        ((5,), 8),
    ],
    "public static int climbStairs(int n)",
    """        if (n <= 2) return n;
        int a = 1, b = 2;
        for (int i = 3; i <= n; i++) {
            int tmp = a + b;
            a = b;
            b = tmp;
        }
        return b""",
    [
        ("2", "2"),
        ("3", "3"),
        ("5", "8"),
    ],
    """`dp[i] = dp[i-1] + dp[i-2]` (Fibonacci). O(1) space with two
rolling variables.

**Time:** O(n). **Space:** O(1).
""",
)

# 2. Min Cost Climbing Stairs (Easy)
add(
    "02-min-cost-climbing-stairs", "Min Cost Climbing Stairs", "Easy",
    "You are given an integer array `cost` where `cost[i]` is the cost of "
    "ith step on a staircase. Once you pay the cost, you can either climb "
    "one or two steps. You can either start from the step with index 0, "
    "or the step with index 1. Return the minimum cost to reach the top "
    "of the floor.",
    [
        ("cost = [10,15,20]", "15"),
        ("cost = [1,100,1,1,1,100,1,1,100,1]", "6"),
    ],
    [
        "2 <= len(cost) <= 1000",
        "0 <= cost[i] <= 999",
    ],
    [
        "`dp[i] = cost[i] + min(dp[i-1], dp[i-2])`.",
    ],
    "def min_cost_climbing_stairs(cost: list[int]) -> int:",
    """    a, b = cost[0], cost[1]
    for i in range(2, len(cost)):
        a, b = b, cost[i] + min(a, b)
    return min(a, b)""",
    [
        (([10, 15, 20],), 15),
        (([1, 100, 1, 1, 1, 100, 1, 1, 100, 1],), 6),
    ],
    "public static int minCostClimbingStairs(int[] cost)",
    """        int a = cost[0], b = cost[1];
        for (int i = 2; i < cost.length; i++) {
            int tmp = b;
            b = cost[i] + Math.min(a, b);
            a = tmp;
        }
        return Math.min(a, b)""",
    [
        ("new int[]{10,15,20}", "15"),
        ("new int[]{1,100,1,1,1,100,1,1,100,1}", "6"),
    ],
    """Same as climbing stairs, but with costs. `dp[i] = cost[i] + min(dp[i-1], dp[i-2])`.

**Time:** O(n). **Space:** O(1).
""",
)

# 3. House Robber (Medium)
add(
    "03-house-robber", "House Robber", "Medium",
    "You are a professional robber planning to rob houses along a street. "
    "Each house has a certain amount of money stashed, the only "
    "constraint stopping you from robbing each of them is that adjacent "
    "houses have security systems connected and **it will automatically "
    "contact the police if two adjacent houses were broken into on the "
    "same night**. Given an integer array `nums` representing the amount "
    "of money at each house, return the maximum amount of money you can "
    "rob tonight **without alerting the police**.",
    [
        ("nums = [1,2,3,1]", "4"),
        ("nums = [2,7,9,3,1]", "12"),
    ],
    [
        "1 <= nums.length <= 100",
        "0 <= nums[i] <= 400",
    ],
    [
        "`dp[i] = max(dp[i-1], dp[i-2] + nums[i])`.",
    ],
    "def rob(nums: list[int]) -> int:",
    """    if not nums: return 0
    if len(nums) == 1: return nums[0]
    a, b = nums[0], max(nums[0], nums[1])
    for i in range(2, len(nums)):
        a, b = b, max(b, a + nums[i])
    return b""",
    [
        (([1, 2, 3, 1],), 4),
        (([2, 7, 9, 3, 1],), 12),
    ],
    "public static int rob(int[] nums)",
    """        if (nums.length == 0) return 0;
        if (nums.length == 1) return nums[0];
        int a = nums[0], b = Math.max(nums[0], nums[1]);
        for (int i = 2; i < nums.length; i++) {
            int tmp = b;
            b = Math.max(b, a + nums[i]);
            a = tmp;
        }
        return b""",
    [
        ("new int[]{1,2,3,1}", "4"),
        ("new int[]{2,7,9,3,1}", "12"),
    ],
    """Standard 1D DP. Two rolling variables: `a` = best through `i-2`,
`b` = best through `i-1`.

**Time:** O(n). **Space:** O(1).
""",
)

# 4. House Robber II (Medium)
add(
    "04-house-robber-ii", "House Robber II", "Medium",
    "Same problem as House Robber, but the houses are arranged in a "
    "**circle**. That means the first and last houses are adjacent.",
    [
        ("nums = [2,3,2]", "3"),
        ("nums = [1,2,3,1]", "4"),
        ("nums = [0]", "0"),
    ],
    [
        "1 <= nums.length <= 100",
        "0 <= nums[i] <= 1000",
    ],
    [
        "Two cases: skip the first, or skip the last. Run House Robber on each.",
    ],
    "def rob_circle(nums: list[int]) -> int:",
    """    if len(nums) == 1: return nums[0]

    def helper(arr):
        a, b = arr[0], max(arr[0], arr[1])
        for i in range(2, len(arr)):
            a, b = b, max(b, a + arr[i])
        return b

    return max(helper(nums[:-1]), helper(nums[1:]))""",
    [
        (([2, 3, 2],), 3),
        (([1, 2, 3, 1],), 4),
        (([0],), 0),
    ],
    "public static int robCircle(int[] nums)",
    """        if (nums.length == 1) return nums[0];
        return Math.max(rob(nums, 0, nums.length - 1), rob(nums, 1, nums.length));
    }

    private static int rob(int[] nums, int lo, int hi) {
        if (lo + 1 >= hi) return nums[lo];
        int a = nums[lo], b = Math.max(nums[lo], nums[lo + 1]);
        for (int i = lo + 2; i < hi; i++) {
            int tmp = b;
            b = Math.max(b, a + nums[i]);
            a = tmp;
        }
        return b;""",
    [
        ("new int[]{2,3,2}", "3"),
        ("new int[]{1,2,3,1}", "4"),
        ("new int[]{0}", "0"),
    ],
    """Two cases: skip the first, or skip the last. Run House Robber on
each subrange.

**Time:** O(n). **Space:** O(1).
""",
)

# 5. Longest Palindromic Substring (Medium)
add(
    "05-longest-palindromic-substring", "Longest Palindromic Substring",
    "Medium",
    "Given a string `s`, return the longest palindromic substring.",
    [
        ("s = 'babad'", "'bab' or 'aba'"),
        ("s = 'cbbd'", "'bb'"),
    ],
    [
        "1 <= len(s) <= 1000",
        "s consist of only digits and English letters",
    ],
    [
        "Expand around each center. A palindrome has 2n-1 possible "
        "centers (between or on characters).",
    ],
    "def longest_palindrome(s: str) -> str:",
    """    def expand(l: int, r: int) -> int:
        while l >= 0 and r < len(s) and s[l] == s[r]:
            l -= 1
            r += 1
        return r - l - 1   # length of the palindrome

    best_l, best_len = 0, 0
    for i in range(len(s)):
        l1 = expand(i, i)
        l2 = expand(i, i + 1)
        m = max(l1, l2)
        if m > best_len:
            best_len = m
            best_l = i - (m - 1) // 2
    return s[best_l:best_l + best_len]""",
    [
        (("babad",), "bab"),
        (("cbbd",), "bb"),
    ],
    "public static String longestPalindrome(String s)",
    """        int bestLo = 0, bestLen = 0;
        for (int i = 0; i < s.length(); i++) {
            int l1 = expand(s, i, i);
            int l2 = expand(s, i, i + 1);
            int m = Math.max(l1, l2);
            if (m > bestLen) {
                bestLen = m;
                bestLo = i - (m - 1) / 2;
            }
        }
        return s.substring(bestLo, bestLo + bestLen);
    }

    private static int expand(String s, int l, int r) {
        while (l >= 0 && r < s.length() && s.charAt(l) == s.charAt(r)) {
            l--; r++;
        }
        return r - l - 1;""",
    [
        ("\"babad\"", "bab"),
        ("\"cbbd\"", "bb"),
    ],
    """Expand around each possible center. A palindrome's center can be
on a character (odd length) or between two (even length).

**Time:** O(n²). **Space:** O(1).
""",
)

# 6. Palindromic Substrings (Medium)
add(
    "06-palindromic-substrings", "Palindromic Substrings", "Medium",
    "Given a string `s`, return the number of palindromic substrings in "
    "it. A string is a palindrome when it reads the same backward as "
    "forward. A substring is a contiguous sequence of characters in the "
    "string.",
    [
        ("s = 'abc'", "3"),
        ("s = 'aaa'", "6"),
    ],
    [
        "1 <= len(s) <= 1000",
        "s consists of lowercase English letters",
    ],
    [
        "Same expand-around-center technique. Count instead of tracking "
        "the longest.",
    ],
    "def count_substrings(s: str) -> int:",
    """    count = 0

    def expand(l: int, r: int) -> None:
        nonlocal count
        while l >= 0 and r < len(s) and s[l] == s[r]:
            count += 1
            l -= 1
            r += 1

    for i in range(len(s)):
        expand(i, i)
        expand(i, i + 1)
    return count""",
    [
        (("abc",), 3),
        (("aaa",), 6),
    ],
    "public static int countSubstrings(String s)",
    """        int count = 0;
        for (int i = 0; i < s.length(); i++) {
            count += expand(s, i, i);
            count += expand(s, i, i + 1);
        }
        return count;
    }

    private static int expand(String s, int l, int r) {
        int c = 0;
        while (l >= 0 && r < s.length() && s.charAt(l) == s.charAt(r)) {
            c++;
            l--; r++;
        }
        return c;""",
    [
        ("\"abc\"", "3"),
        ("\"aaa\"", "6"),
    ],
    """Same expand-around-center. Count each palindrome as we expand.

**Time:** O(n²). **Space:** O(1).
""",
)

# 7. Decode Ways (Medium)
add(
    "07-decode-ways", "Decode Ways", "Medium",
    "You have intercepted a secret message encoded as a string of digits "
    "0-9 representing letters A-Z (1=A, ..., 26=Z). Return the number of "
    "ways to decode it.",
    [
        ("s = '12'", "2"),  # AB, L
        ("s = '226'", "3"),
        ("s = '06'", "0"),
    ],
    [
        "1 <= len(s) <= 100",
        "s contains only digits",
    ],
    [
        "`dp[i] = number of ways to decode s[:i]`. `dp[i] = dp[i-1]` if "
        "`s[i-1]` is non-zero; `dp[i] += dp[i-2]` if `s[i-2:i]` is in [10, 26].",
    ],
    "def num_decodings(s: str) -> int:",
    """    if not s or s[0] == '0': return 0
    dp0, dp1 = 1, 1
    for i in range(1, len(s)):
        cur = 0
        if s[i] != '0':
            cur += dp1
        two = int(s[i - 1:i + 1])
        if 10 <= two <= 26:
            cur += dp0
        dp0, dp1 = dp1, cur
    return dp1""",
    [
        (("12",), 2),
        (("226",), 3),
        (("06",), 0),
        (("10",), 1),
    ],
    "public static int numDecodings(String s)",
    """        if (s.isEmpty() || s.charAt(0) == '0') return 0;
        int dp0 = 1, dp1 = 1;
        for (int i = 1; i < s.length(); i++) {
            int cur = 0;
            if (s.charAt(i) != '0') cur += dp1;
            int two = Integer.parseInt(s.substring(i - 1, i + 1));
            if (10 <= two && two <= 26) cur += dp0;
            dp0 = dp1;
            dp1 = cur;
        }
        return dp1;""",
    [
        ("\"12\"", "2"),
        ("\"226\"", "3"),
    ],
    """Two rolling variables. `dp[i]` is the number of ways to decode
`s[:i]`. The transition depends on `s[i-1]` (single digit) and
`s[i-2:i]` (two-digit pair).

**Time:** O(n). **Space:** O(1).
""",
)

# 8. Coin Change (Medium)
add(
    "08-coin-change", "Coin Change", "Medium",
    "Given an array `coins` representing coin denominations and an "
    "integer `amount`, return the fewest number of coins needed to make "
    "up that amount. Return -1 if it's impossible.",
    [
        ("coins = [1,5,10,25], amount = 30", "2"),  # 5+25 or 10+10+10
        ("coins = [2], amount = 3", "-1"),
    ],
    [
        "1 <= coins.length <= 12",
        "1 <= coins[i] <= 2^31 - 1",
        "0 <= amount <= 10^4",
    ],
    [
        "`dp[a] = min(dp[a], dp[a - c] + 1) for c in coins`.",
    ],
    "def coin_change(coins: list[int], amount: int) -> int:",
    """    dp = [float('inf')] * (amount + 1)
    dp[0] = 0
    for c in coins:
        for a in range(c, amount + 1):
            if dp[a - c] + 1 < dp[a]:
                dp[a] = dp[a - c] + 1
    return dp[amount] if dp[amount] != float('inf') else -1""",
    [
        (([1, 5, 10, 25], 30), 2),
        (([2], 3), -1),
        (([1], 0), 0),
        (([186, 419, 83, 408], 6249), 20),
    ],
    "public static int coinChange(int[] coins, int amount)",
    """        int[] dp = new int[amount + 1];
        Arrays.fill(dp, amount + 1);
        dp[0] = 0;
        for (int c : coins) {
            for (int a = c; a <= amount; a++) {
                if (dp[a - c] + 1 < dp[a]) dp[a] = dp[a - c] + 1;
            }
        }
        return dp[amount] == amount + 1 ? -1 : dp[amount];""",
    [
        ("new int[]{1,5,10,25}, 30", "2"),
        ("new int[]{2}, 3", "-1"),
    ],
    """Bottom-up DP. `dp[a]` = min coins to make `a`. We try each coin
and update.

**Time:** O(n · amount). **Space:** O(amount).
""",
)

# 9. Maximum Product Subarray (Medium)
add(
    "09-maximum-product-subarray", "Maximum Product Subarray", "Medium",
    "Given an integer array `nums`, find a subarray that has the largest "
    "product, and return the product.",
    [
        ("nums = [2,3,-2,4]", "6"),
        ("nums = [-2,0,-1]", "0"),
    ],
    [
        "1 <= len(nums) <= 2 * 10^4",
        "-10 <= nums[i] <= 10",
    ],
    [
        "Track both max and min products: a negative flips them.",
    ],
    "def max_product(nums: list[int]) -> int:",
    """    best = max_end = min_end = nums[0]
    for i in range(1, len(nums)):
        x = nums[i]
        if x < 0:
            max_end, min_end = min_end, max_end
        max_end = max(x, max_end * x)
        min_end = min(x, min_end * x)
        best = max(best, max_end)
    return best""",
    [
        (([2, 3, -2, 4],), 6),
        (([-2, 0, -1],), 0),
        (([-2],), -2),
    ],
    "public static int maxProduct(int[] nums)",
    """        int best = nums[0], maxEnd = nums[0], minEnd = nums[0];
        for (int i = 1; i < nums.length; i++) {
            int x = nums[i];
            if (x < 0) { int t = maxEnd; maxEnd = minEnd; minEnd = t; }
            maxEnd = Math.max(x, maxEnd * x);
            minEnd = Math.min(x, minEnd * x);
            best = Math.max(best, maxEnd);
        }
        return best;""",
    [
        ("new int[]{2,3,-2,4}", "6"),
        ("new int[]{-2,0,-1}", "0"),
    ],
    """Track both max and min ending at the current position. On a
negative, swap them. The min can become the max after a sign flip.

**Time:** O(n). **Space:** O(1).
""",
)

# 10. Word Break (Medium)
add(
    "10-word-break", "Word Break", "Medium",
    "Given a string `s` and a dictionary of strings `wordDict`, return "
    "`True` if `s` can be segmented into a space-separated sequence of "
    "one or more dictionary words.",
    [
        ("s = 'leetcode', wordDict = ['leet','code']", "True"),
        ("s = 'applepenapple', wordDict = ['apple','pen']", "True"),
        ("s = 'catsandog', wordDict = ['cats','dog','sand','and','cat']", "False"),
    ],
    [
        "1 <= len(s) <= 300",
        "1 <= wordDict.length <= 1000",
        "1 <= wordDict[i].length <= 20",
        "s and wordDict[i] consist of only lowercase English letters",
    ],
    [
        "`dp[i] = True` if `s[:i]` can be segmented. For each `j < i` "
        "with `dp[j] = True` and `s[j:i]` in the dict, set `dp[i] = True`.",
    ],
    "def word_break(s: str, word_dict: list[str]) -> bool:",
    """    word_set = set(word_dict)
    n = len(s)
    dp = [False] * (n + 1)
    dp[0] = True
    for i in range(1, n + 1):
        for j in range(i):
            if dp[j] and s[j:i] in word_set:
                dp[i] = True
                break
    return dp[n]""",
    [
        (("leetcode", ["leet", "code"]), True),
        (("applepenapple", ["apple", "pen"]), True),
        (("catsandog", ["cats","dog","sand","and","cat"]), False),
    ],
    "public static boolean wordBreak(String s, List<String> wordDict)",
    """        Set<String> wordSet = new HashSet<>(wordDict);
        int n = s.length();
        boolean[] dp = new boolean[n + 1];
        dp[0] = true;
        for (int i = 1; i <= n; i++) {
            for (int j = 0; j < i; j++) {
                if (dp[j] && wordSet.contains(s.substring(j, i))) {
                    dp[i] = true;
                    break;
                }
            }
        }
        return dp[n];""",
    [
        ("\"leetcode\", List.of(\"leet\",\"code\")", "true"),
        ("\"catsandog\", List.of(\"cats\",\"dog\",\"sand\",\"and\",\"cat\")", "false"),
    ],
    """Bottom-up DP. `dp[i]` = can segment `s[:i]`. For each `i`, try
each `j < i` and check if `s[j:i]` is in the dict.

**Time:** O(n² · L) where L is the average word length. **Space:** O(n).
""",
)

# 11. Longest Increasing Subsequence (Medium)
add(
    "11-longest-increasing-subsequence", "Longest Increasing Subsequence",
    "Medium",
    "Given an integer array `nums`, return the length of the longest "
    "**strictly increasing** subsequence.",
    [
        ("nums = [10,9,2,5,3,7,101,18]", "4"),
        ("nums = [0,1,0,3,2,3]", "4"),
        ("nums = [7,7,7,7,7,7,7]", "1"),
    ],
    [
        "1 <= len(nums) <= 2500",
        "-10^4 <= nums[i] <= 10^4",
    ],
    [
        "Standard O(n²) DP: `dp[i] = max(dp[j] + 1)` for `j < i` and "
        "`nums[j] < nums[i]`.",
        "O(n log n) with patience sorting: `bisect_left` on a 'tails' array.",
    ],
    "def length_of_lis(nums: list[int]) -> int:",
    """    import bisect
    tails: list[int] = []
    for x in nums:
        i = bisect.bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)""",
    [
        (([10, 9, 2, 5, 3, 7, 101, 18],), 4),
        (([0, 1, 0, 3, 2, 3],), 4),
        (([7, 7, 7, 7, 7, 7, 7],), 1),
    ],
    "public static int lengthOfLIS(int[] nums)",
    """        int[] tails = new int[nums.length];
        int size = 0;
        for (int x : nums) {
            int lo = 0, hi = size;
            while (lo < hi) {
                int mid = (lo + hi) / 2;
                if (tails[mid] < x) lo = mid + 1; else hi = mid;
            }
            tails[lo] = x;
            if (lo == size) size++;
        }
        return size;""",
    [
        ("new int[]{10,9,2,5,3,7,101,18}", "4"),
        ("new int[]{0,1,0,3,2,3}", "4"),
    ],
    """**Patience sorting.** Maintain a `tails` array: the smallest
tail of an increasing subsequence of each length. `bisect_left` finds
where to update.

**Time:** O(n log n). **Space:** O(n).
""",
)

# 12. Partition Equal Subset Sum (Medium)
add(
    "12-partition-equal-subset-sum", "Partition Equal Subset Sum", "Medium",
    "Given a non-empty array `nums` containing only positive integers, "
    "find if the array can be partitioned into two subsets such that the "
    "sum of elements in both subsets is equal.",
    [
        ("nums = [1,5,11,5]", "True"),
        ("nums = [1,2,3,5]", "False"),
    ],
    [
        "1 <= len(nums) <= 200",
        "1 <= nums[i] <= 100",
    ],
    [
        "Reduce to subset sum: can we hit `total / 2`?",
    ],
    "def can_partition(nums: list[int]) -> bool:",
    """    total = sum(nums)
    if total % 2: return False
    target = total // 2
    dp = [False] * (target + 1)
    dp[0] = True
    for x in nums:
        for s in range(target, x - 1, -1):
            if dp[s - x]:
                dp[s] = True
    return dp[target]""",
    [
        (([1, 5, 11, 5],), True),
        (([1, 2, 3, 5],), False),
        (([2, 2],), True),
    ],
    "public static boolean canPartition(int[] nums)",
    """        int total = 0;
        for (int x : nums) total += x;
        if ((total & 1) == 1) return false;
        int target = total / 2;
        boolean[] dp = new boolean[target + 1];
        dp[0] = true;
        for (int x : nums) {
            for (int s = target; s >= x; s--) {
                if (dp[s - x]) dp[s] = true;
            }
        }
        return dp[target];""",
    [
        ("new int[]{1,5,11,5}", "true"),
        ("new int[]{1,2,3,5}", "false"),
    ],
    """Subset-sum DP. The target is `total / 2` (must be even). Each
number is either in or out of the subset.

**Time:** O(n · sum). **Space:** O(sum).
""",
)

# 13. Unique Paths (Medium)
add(
    "13-unique-paths", "Unique Paths", "Medium",
    "There is a robot on an `m x n` grid. The robot is initially located "
    "at the top-left corner (i.e., `grid[0][0]`). The robot tries to move "
    "to the bottom-right corner (i.e., `grid[m - 1][n - 1]`). The robot "
    "can only move either down or right at any point in time. Given the "
    "two integers `m` and `n`, return the number of possible unique paths "
    "that the robot can take to reach the bottom-right corner.",
    [
        ("m = 3, n = 7", "28"),
        ("m = 3, n = 2", "3"),
    ],
    [
        "1 <= m, n <= 100",
    ],
    [
        "`dp[i][j] = dp[i-1][j] + dp[i][j-1]` (combinatorics: C(m+n-2, m-1)).",
    ],
    "def unique_paths(m: int, n: int) -> int:",
    """    row = [1] * n
    for i in range(1, m):
        for j in range(1, n):
            row[j] += row[j - 1]
    return row[-1]""",
    [
        ((3, 7), 28),
        ((3, 2), 3),
    ],
    "public static int uniquePaths(int m, int n)",
    """        int[] row = new int[n];
        Arrays.fill(row, 1);
        for (int i = 1; i < m; i++) {
            for (int j = 1; j < n; j++) {
                row[j] += row[j - 1];
            }
        }
        return row[n - 1];""",
    [
        ("3, 7", "28"),
        ("3, 2", "3"),
    ],
    """`dp[i][j] = dp[i-1][j] + dp[i][j-1]`. We only need one row of
rolling state.

**Time:** O(m · n). **Space:** O(n).
""",
)

# 14. Longest Common Subsequence (Medium)
add(
    "14-longest-common-subsequence", "Longest Common Subsequence", "Medium",
    "Given two strings `text1` and `text2`, return the length of their "
    "longest **common subsequence**. A *subsequence* of a string is a new "
    "string generated from the original string with some characters (can "
    "be none) deleted without changing the relative order of the "
    "remaining characters.",
    [
        ("text1 = 'abcde', text2 = 'ace'", "3"),
        ("text1 = 'abc', text2 = 'abc'", "3"),
        ("text1 = 'abc', text2 = 'def'", "0"),
    ],
    [
        "1 <= len(text1), len(text2) <= 1000",
    ],
    [
        "`dp[i][j] = dp[i-1][j-1] + 1` if chars match, else "
        "`max(dp[i-1][j], dp[i][j-1])`.",
    ],
    "def longest_common_subsequence(text1: str, text2: str) -> int:",
    """    m, n = len(text1), len(text2)
    dp = [0] * (n + 1)
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            tmp = dp[j]
            if text1[i - 1] == text2[j - 1]:
                dp[j] = prev + 1
            else:
                dp[j] = max(dp[j], dp[j - 1])
            prev = tmp
    return dp[n]""",
    [
        (("abcde", "ace"), 3),
        (("abc", "abc"), 3),
        (("abc", "def"), 0),
    ],
    "public static int longestCommonSubsequence(String text1, String text2)",
    """        int m = text1.length(), n = text2.length();
        int[] dp = new int[n + 1];
        for (int i = 1; i <= m; i++) {
            int prev = 0;
            for (int j = 1; j <= n; j++) {
                int tmp = dp[j];
                if (text1.charAt(i - 1) == text2.charAt(j - 1)) dp[j] = prev + 1;
                else dp[j] = Math.max(dp[j], dp[j - 1]);
                prev = tmp;
            }
        }
        return dp[n];""",
    [
        ("\"abcde\", \"ace\"", "3"),
        ("\"abc\", \"abc\"", "3"),
    ],
    """Classic 2D DP, reduced to one row. The `prev` variable holds
`dp[i-1][j-1]` from the previous row.

**Time:** O(m · n). **Space:** O(n).
""",
)

# 15. Best Time to Buy and Sell Stock with Cooldown (Medium)
add(
    "15-best-time-to-buy-and-sell-stock-with-cooldown",
    "Best Time to Buy and Sell Stock with Cooldown", "Medium",
    "You are given an array `prices` where `prices[i]` is the price of a "
    "given stock on the ith day. Find the maximum profit you can achieve. "
    "You may complete as many transactions as you like (i.e., buy one and "
    "sell one share of the stock multiple times) with the following "
    "**restrictions**: After you sell your stock, you cannot buy stock on "
    "the next day (i.e., cooldown one day).",
    [
        ("prices = [1,2,3,0,2]", "3"),
        ("prices = [1]", "0"),
    ],
    [
        "1 <= len(prices) <= 5000",
        "0 <= prices[i] <= 1000",
    ],
    [
        "Three states: hold, sold (just sold, in cooldown), free (no "
        "stock, no cooldown).",
    ],
    "def max_profit_cooldown(prices: list[int]) -> int:",
    """    n = len(prices)
    if n < 2: return 0
    free = 0
    hold = -prices[0]
    sold = 0
    for i in range(1, n):
        new_free = max(free, sold)
        new_sold = hold + prices[i]
        new_hold = max(hold, free - prices[i])
        free, sold, hold = new_free, new_sold, new_hold
    return max(free, sold)""",
    [
        (([1, 2, 3, 0, 2],), 3),
        (([1],), 0),
    ],
    "public static int maxProfitCooldown(int[] prices)",
    """        int n = prices.length;
        if (n < 2) return 0;
        int free = 0, hold = -prices[0], sold = 0;
        for (int i = 1; i < n; i++) {
            int newFree = Math.max(free, sold);
            int newSold = hold + prices[i];
            int newHold = Math.max(hold, free - prices[i]);
            free = newFree; sold = newSold; hold = newHold;
        }
        return Math.max(free, sold);""",
    [
        ("new int[]{1,2,3,0,2}", "3"),
        ("new int[]{1}", "0"),
    ],
    """Three rolling states. `free` = no stock no cooldown; `hold` =
holding a stock; `sold` = just sold (will become `free` tomorrow).

**Time:** O(n). **Space:** O(1).
""",
)

# 16. Coin Change II (Medium)
add(
    "16-coin-change-ii", "Coin Change II", "Medium",
    "Given an array of **distinct** integers `coins` and an integer "
    "`amount`, return the number of combinations that make up that "
    "amount. You may use each coin unlimited times. The order of coins "
    "doesn't matter.",
    [
        ("amount = 5, coins = [1,2,5]", "4"),
        ("amount = 3, coins = [2]", "0"),
        ("amount = 10, coins = [10]", "1"),
    ],
    [
        "1 <= coins.length <= 300",
        "1 <= coins[i] <= 5000",
        "All coins are unique",
        "0 <= amount <= 5000",
    ],
    [
        "Outer loop on coins, inner loop on amount. This ordering ensures "
        "each combination is counted once.",
    ],
    "def change(amount: int, coins: list[int]) -> int:",
    """    dp = [0] * (amount + 1)
    dp[0] = 1
    for c in coins:
        for a in range(c, amount + 1):
            dp[a] += dp[a - c]
    return dp[amount]""",
    [
        ((5, [1, 2, 5]), 4),
        ((3, [2]), 0),
        ((10, [10]), 1),
    ],
    "public static int change(int amount, int[] coins)",
    """        int[] dp = new int[amount + 1];
        dp[0] = 1;
        for (int c : coins) {
            for (int a = c; a <= amount; a++) {
                dp[a] += dp[a - c];
            }
        }
        return dp[amount];""",
    [
        ("5, new int[]{1,2,5}", "4"),
        ("3, new int[]{2}", "0"),
    ],
    """Outer loop over coins. Each combination is built up in a
canonical order (smallest coin first), so we don't double-count.

**Time:** O(n · amount). **Space:** O(amount).
""",
)

# 17. Target Sum (Medium)
add(
    "17-target-sum", "Target Sum", "Medium",
    "You are given an integer array `nums` and an integer `target`. You "
    "want to build an expression by placing a `+` or `-` sign in front "
    "of each integer in `nums` and then concatenate all the signed "
    "integers. Return the number of different expressions that you can "
    "build, which evaluate to `target`.",
    [
        ("nums = [1,1,1,1,1], target = 3", "5"),
        ("nums = [1], target = 1", "1"),
    ],
    [
        "1 <= nums.length <= 20",
        "0 <= nums[i] <= 1000",
        "0 <= sum(nums[i]) <= 1000",
        "-1000 <= target <= 1000",
    ],
    [
        "Reduce to subset sum: partition nums into positive and negative "
        "groups. The sum condition becomes a subset-sum problem.",
    ],
    "def find_target_sum_ways(nums: list[int], target: int) -> int:",
    """    total = sum(nums)
    if abs(target) > total: return 0
    if (total + target) % 2: return 0
    p = (total + target) // 2
    dp = [0] * (p + 1)
    dp[0] = 1
    for x in nums:
        for s in range(p, x - 1, -1):
            dp[s] += dp[s - x]
    return dp[p]""",
    [
        (([1, 1, 1, 1, 1], 3), 5),
        (([1], 1), 1),
    ],
    "public static int findTargetSumWays(int[] nums, int target)",
    """        int total = 0;
        for (int x : nums) total += x;
        if (Math.abs(target) > total) return 0;
        if (((total + target) & 1) == 1) return 0;
        int p = (total + target) / 2;
        int[] dp = new int[p + 1];
        dp[0] = 1;
        for (int x : nums) {
            for (int s = p; s >= x; s--) {
                dp[s] += dp[s - x];
            }
        }
        return dp[p];""",
    [
        ("new int[]{1,1,1,1,1}, 3", "5"),
        ("new int[]{1}, 1", "1"),
    ],
    """Let `P` be the sum of positive-signed numbers, `N` negative.
`P - N = target` and `P + N = total`, so `P = (total + target) / 2`.
Count subsets summing to `P`.

**Time:** O(n · total). **Space:** O(total).
""",
)

# 18. Interleaving String (Medium)
add(
    "18-interleaving-string", "Interleaving String", "Medium",
    "Given strings `s1`, `s2`, and `s3`, find whether `s3` is formed by "
    "an interleaving of `s1` and `s2`. An interleaving of two strings `s` "
    "and `t` is a configuration where `s` and `t` are divided into "
    "non-empty substrings respectively, and the resulting string is `s` "
    "and `t` concatenated.",
    [
        ("s1 = 'aabcc', s2 = 'dbbca', s3 = 'aadbbcbcac'", "True"),
        ("s1 = 'aabcc', s2 = 'dbbca', s3 = 'aadbbbaccc'", "False"),
    ],
    [
        "0 <= len(s1), len(s2) <= 100",
        "0 <= len(s3) <= 200",
        "s1, s2, s3 consist of lowercase English letters",
    ],
    [
        "`dp[i][j]` = can `s3[:i+j]` be formed by interleaving "
        "`s1[:i]` and `s2[:j]`.",
    ],
    "def is_interleave(s1: str, s2: str, s3: str) -> bool:",
    """    if len(s1) + len(s2) != len(s3): return False
    m, n = len(s1), len(s2)
    dp = [False] * (n + 1)
    dp[0] = True
    for j in range(1, n + 1):
        dp[j] = dp[j - 1] and s2[j - 1] == s3[j - 1]
    for i in range(1, m + 1):
        dp[0] = dp[0] and s1[i - 1] == s3[i - 1]
        for j in range(1, n + 1):
            dp[j] = (dp[j] and s1[i - 1] == s3[i + j - 1]) or \\
                    (dp[j - 1] and s2[j - 1] == s3[i + j - 1])
    return dp[n]""",
    [
        (("aabcc", "dbbca", "aadbbcbcac"), True),
        (("aabcc", "dbbca", "aadbbbaccc"), False),
        (("", "", ""), True),
    ],
    "public static boolean isInterleave(String s1, String s2, String s3)",
    """        int m = s1.length(), n = s2.length();
        if (m + n != s3.length()) return false;
        boolean[] dp = new boolean[n + 1];
        dp[0] = true;
        for (int j = 1; j <= n; j++) dp[j] = dp[j - 1] && s2.charAt(j - 1) == s3.charAt(j - 1);
        for (int i = 1; i <= m; i++) {
            dp[0] = dp[0] && s1.charAt(i - 1) == s3.charAt(i - 1);
            for (int j = 1; j <= n; j++) {
                dp[j] = (dp[j] && s1.charAt(i - 1) == s3.charAt(i + j - 1))
                      || (dp[j - 1] && s2.charAt(j - 1) == s3.charAt(i + j - 1));
            }
        }
        return dp[n];""",
    [
        ("\"aabcc\", \"dbbca\", \"aadbbcbcac\"", "true"),
        ("\"aabcc\", \"dbbca\", \"aadbbbaccc\"", "false"),
    ],
    """2D DP reduced to one row. `dp[i][j]` = can `s1[:i]` and `s2[:j]`
form `s3[:i+j]`.

**Time:** O(m · n). **Space:** O(n).
""",
)

# 19. Edit Distance (Medium)
add(
    "19-edit-distance", "Edit Distance", "Medium",
    "Given two strings `word1` and `word2`, return the minimum number of "
    "operations required to convert `word1` to `word2`. You have the "
    "following three operations permitted on a word: insert, delete, or "
    "replace a character.",
    [
        ("word1 = 'horse', word2 = 'ros'", "3"),
        ("word1 = 'intention', word2 = 'execution'", "5"),
    ],
    [
        "0 <= word1.length, word2.length <= 500",
        "word1 and word2 consist of lowercase English letters",
    ],
    [
        "`dp[i][j] = dp[i-1][j-1]` if chars match; else `1 + min(dp[i-1][j], "
        "dp[i][j-1], dp[i-1][j-1])`.",
    ],
    "def min_distance(word1: str, word2: str) -> int:",
    """    m, n = len(word1), len(word2)
    dp = list(range(n + 1))
    for i in range(1, m + 1):
        prev = dp[0]
        dp[0] = i
        for j in range(1, n + 1):
            tmp = dp[j]
            if word1[i - 1] == word2[j - 1]:
                dp[j] = prev
            else:
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
            prev = tmp
    return dp[n]""",
    [
        (("horse", "ros"), 3),
        (("intention", "execution"), 5),
    ],
    "public static int minDistance(String word1, String word2)",
    """        int m = word1.length(), n = word2.length();
        int[] dp = new int[n + 1];
        for (int j = 0; j <= n; j++) dp[j] = j;
        for (int i = 1; i <= m; i++) {
            int prev = dp[0];
            dp[0] = i;
            for (int j = 1; j <= n; j++) {
                int tmp = dp[j];
                if (word1.charAt(i - 1) == word2.charAt(j - 1)) dp[j] = prev;
                else dp[j] = 1 + Math.min(Math.min(prev, dp[j]), dp[j - 1]);
                prev = tmp;
            }
        }
        return dp[n];""",
    [
        ("\"horse\", \"ros\"", "3"),
        ("\"intention\", \"execution\"", "5"),
    ],
    """Classic edit distance. Three operations: insert, delete,
replace. The recurrence picks the minimum.

**Time:** O(m · n). **Space:** O(n).
""",
)

# 20. Best Time to Buy and Sell Stock III (Hard)
add(
    "20-best-time-to-buy-and-sell-stock-iii",
    "Best Time to Buy and Sell Stock III", "Hard",
    "You are given an array `prices` where `prices[i]` is the price of a "
    "given stock on the ith day. Find the maximum profit you can achieve. "
    "You may complete **at most two transactions**. Note: You may not "
    "engage in multiple transactions simultaneously (i.e., you must sell "
    "the stock before you buy again).",
    [
        ("prices = [3,3,5,0,0,3,1,4]", "6"),
        ("prices = [1,2,3,4,5]", "4"),
    ],
    [
        "1 <= len(prices) <= 10^5",
        "0 <= prices[i] <= 10^5",
    ],
    [
        "DP with four states: buy1, sell1, buy2, sell2.",
    ],
    "def max_profit_two(prices: list[int]) -> int:",
    """    buy1 = sell1 = buy2 = sell2 = float('-inf') if False else 0
    # Use the standard 4-state DP
    buy1 = -prices[0]
    sell1 = 0
    buy2 = -prices[0]
    sell2 = 0
    for i in range(1, len(prices)):
        p = prices[i]
        buy1 = max(buy1, -p)
        sell1 = max(sell1, buy1 + p)
        buy2 = max(buy2, sell1 - p)
        sell2 = max(sell2, buy2 + p)
    return sell2""",
    [
        (([3, 3, 5, 0, 0, 3, 1, 4],), 6),
        (([1, 2, 3, 4, 5],), 4),
    ],
    "public static int maxProfitTwo(int[] prices)",
    """        int buy1 = -prices[0], sell1 = 0;
        int buy2 = -prices[0], sell2 = 0;
        for (int i = 1; i < prices.length; i++) {
            int p = prices[i];
            buy1 = Math.max(buy1, -p);
            sell1 = Math.max(sell1, buy1 + p);
            buy2 = Math.max(buy2, sell1 - p);
            sell2 = Math.max(sell2, buy2 + p);
        }
        return sell2;""",
    [
        ("new int[]{3,3,5,0,0,3,1,4}", "6"),
        ("new int[]{1,2,3,4,5}", "4"),
    ],
    """Four states. `buy1`: best profit after first buy; `sell1`: best
profit after first sell; `buy2`: best after second buy; `sell2`: best
after second sell.

**Time:** O(n). **Space:** O(1).
""",
)

# 21. Best Time to Buy and Sell Stock IV (Hard)
add(
    "21-best-time-to-buy-and-sell-stock-iv",
    "Best Time to Buy and Sell Stock IV", "Hard",
    "You are given an integer array `prices` where `prices[i]` is the "
    "price of a given stock on the ith day, and an integer `k`. Find the "
    "maximum profit you can achieve. You may complete at most `k` "
    "transactions.",
    [
        ("k = 2, prices = [2,4,1]", "2"),
        ("k = 2, prices = [3,2,6,5,0,3]", "7"),
    ],
    [
        "0 <= k <= 100",
        "0 <= len(prices) <= 1000",
        "0 <= prices[i] <= 1000",
    ],
    [
        "DP with `k` pairs of (buy, sell) states. If `k >= n // 2`, the "
        "transactions-unlimited answer applies (just sum the ups).",
    ],
    "def max_profit_k(k: int, prices: list[int]) -> int:",
    """    n = len(prices)
    if k >= n // 2:
        # unlimited transactions
        s = 0
        for i in range(1, n):
            if prices[i] > prices[i - 1]:
                s += prices[i] - prices[i - 1]
        return s
    # DP with k transactions
    buy = [-float('inf')] * (k + 1)
    sell = [0] * (k + 1)
    for p in prices:
        for j in range(1, k + 1):
            buy[j] = max(buy[j], sell[j - 1] - p)
            sell[j] = max(sell[j], buy[j] + p)
    return sell[k]""",
    [
        ((2, [2, 4, 1]), 2),
        ((2, [3, 2, 6, 5, 0, 3]), 7),
    ],
    "public static int maxProfitK(int k, int[] prices)",
    """        int n = prices.length;
        if (k >= n / 2) {
            int s = 0;
            for (int i = 1; i < n; i++) if (prices[i] > prices[i - 1]) s += prices[i] - prices[i - 1];
            return s;
        }
        int[] buy = new int[k + 1];
        int[] sell = new int[k + 1];
        Arrays.fill(buy, Integer.MIN_VALUE);
        for (int p : prices) {
            for (int j = 1; j <= k; j++) {
                buy[j] = Math.max(buy[j], sell[j - 1] - p);
                sell[j] = Math.max(sell[j], buy[j] + p);
            }
        }
        return sell[k];""",
    [
        ("2, new int[]{2,4,1}", "2"),
        ("2, new int[]{3,2,6,5,0,3}", "7"),
    ],
    """Two arrays of size k+1: `buy[j]` and `sell[j]`. For each price,
update all `j`. If `k >= n / 2`, the unlimited answer applies.

**Time:** O(n · k). **Space:** O(k).
""",
)

# 22. Maximal Square (Hard)
add(
    "22-maximal-square", "Maximal Square", "Hard",
    "Given an `m x n` binary matrix `filled` with '0's and '1's, find the "
    "largest square containing only '1's and return its area.",
    [
        ("matrix = [['1','0','1','0','0'],['1','0','1','1','1'],"
         "['1','1','1','1','1'],['1','0','0','1','0']]", "4"),
        ("matrix = [['0','1'],['1','0']]", "1"),
    ],
    [
        "m == matrix.length, n == matrix[i].length",
        "1 <= m, n <= 300",
        "matrix[i][j] is '0' or '1'",
    ],
    [
        "`dp[i][j]` = side of largest square with bottom-right at "
        "`(i, j)`. `dp[i][j] = 1 + min(dp[i-1][j], dp[i][j-1], "
        "dp[i-1][j-1])` if `matrix[i][j] == 1`.",
    ],
    "def maximal_square(matrix: list[list[str]]) -> int:",
    """    m, n = len(matrix), len(matrix[0])
    dp = [0] * (n + 1)
    best = 0
    for i in range(1, m + 1):
        prev = 0
        for j in range(1, n + 1):
            tmp = dp[j]
            if matrix[i - 1][j - 1] == '1':
                dp[j] = 1 + min(prev, dp[j], dp[j - 1])
                best = max(best, dp[j])
            else:
                dp[j] = 0
            prev = tmp
    return best * best""",
    [
        (([["1","0","1","0","0"],["1","0","1","1","1"],["1","1","1","1","1"],["1","0","0","1","0"]],), 4),
        (([["0","1"],["1","0"]],), 1),
    ],
    "public static int maximalSquare(char[][] matrix)",
    """        int m = matrix.length, n = matrix[0].length;
        int[] dp = new int[n + 1];
        int best = 0;
        for (int i = 1; i <= m; i++) {
            int prev = 0;
            for (int j = 1; j <= n; j++) {
                int tmp = dp[j];
                if (matrix[i - 1][j - 1] == '1') {
                    dp[j] = 1 + Math.min(Math.min(prev, dp[j]), dp[j - 1]);
                    best = Math.max(best, dp[j]);
                } else dp[j] = 0;
                prev = tmp;
            }
        }
        return best * best;""",
    [
        ("new char[][]{{'1','0','1','0','0'},{'1','0','1','1','1'},{'1','1','1','1','1'},{'1','0','0','1','0'}}", "4"),
    ],
    """`dp[i][j]` = side of largest square ending at `(i, j)`. The
recurrence is the minimum of the three neighbors + 1. Return `best²`.

**Time:** O(m · n). **Space:** O(n).
""",
)
