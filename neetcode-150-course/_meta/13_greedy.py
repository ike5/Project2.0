"""Module 13 — Greedy problem catalog."""

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


# 1. Maximum Subarray (Easy)
add(
    "01-maximum-subarray", "Maximum Subarray", "Easy",
    "Given an integer array `nums`, find the subarray with the largest "
    "sum, and return its sum.",
    [
        ("nums = [-2,1,-3,4,-1,2,1,-5,4]", "6"),  # [4,-1,2,1]
        ("nums = [1]", "1"),
        ("nums = [5,4,-1,7,8]", "23"),
    ],
    [
        "1 <= len(nums) <= 10^5",
        "-10^4 <= nums[i] <= 10^4",
    ],
    [
        "Kadane's algorithm: keep a running sum; reset to 0 when it "
        "goes negative.",
    ],
    "def max_subarray(nums: list[int]) -> int:",
    """    best = cur = nums[0]
    for x in nums[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best""",
    [
        (([-2, 1, -3, 4, -1, 2, 1, -5, 4],), 6),
        (([1],), 1),
        (([5, 4, -1, 7, 8],), 23),
    ],
    "public static int maxSubarray(int[] nums)",
    """        int best = nums[0], cur = nums[0];
        for (int i = 1; i < nums.length; i++) {
            cur = Math.max(nums[i], cur + nums[i]);
            best = Math.max(best, cur);
        }
        return best;""",
    [
        ("new int[]{-2,1,-3,4,-1,2,1,-5,4}", "6"),
        ("new int[]{1}", "1"),
    ],
    """Kadane. `cur` = best sum ending at the current position. We
either extend the previous best (`cur + x`) or start fresh at `x`.

**Time:** O(n). **Space:** O(1).
""",
)

# 2. Jump Game (Medium)
add(
    "02-jump-game", "Jump Game", "Medium",
    "You are given an integer array `nums`. You are initially positioned "
    "at the array's **first index**, and each element in the array "
    "represents your maximum jump length at that position. Return `True` "
    "if you can reach the last index, or `False` otherwise.",
    [
        ("nums = [2,3,1,1,4]", "True"),
        ("nums = [3,2,1,0,4]", "False"),
    ],
    [
        "1 <= len(nums) <= 10^4",
        "0 <= nums[i] <= 10^5",
    ],
    [
        "Track the farthest reachable index as you go.",
    ],
    "def can_jump(nums: list[int]) -> bool:",
    """    farthest = 0
    for i, x in enumerate(nums):
        if i > farthest:
            return False
        farthest = max(farthest, i + x)
    return True""",
    [
        (([2, 3, 1, 1, 4],), True),
        (([3, 2, 1, 0, 4],), False),
        (([0],), True),
    ],
    "public static boolean canJump(int[] nums)",
    """        int farthest = 0;
        for (int i = 0; i < nums.length; i++) {
            if (i > farthest) return false;
            farthest = Math.max(farthest, i + nums[i]);
        }
        return true;""",
    [
        ("new int[]{2,3,1,1,4}", "true"),
        ("new int[]{3,2,1,0,4}", "false"),
    ],
    """Greedy. `farthest` = the rightmost index we can reach so far. If
at any point `i > farthest`, we're stuck.

**Time:** O(n). **Space:** O(1).
""",
)

# 3. Jump Game II (Medium)
add(
    "03-jump-game-ii", "Jump Game II", "Medium",
    "You are given a **0-indexed** array of integers `nums` of length "
    "`n`. You are initially positioned at `nums[0]`. Each element "
    "`nums[i]` represents the maximum jump length from that index. "
    "Return the minimum number of jumps to reach `nums[n - 1]`. The test "
    "cases are generated such that you can reach `nums[n - 1]`.",
    [
        ("nums = [2,3,1,1,4]", "2"),
        ("nums = [2,3,0,1,4]", "2"),
    ],
    [
        "1 <= len(nums) <= 10^4",
        "0 <= nums[i] <= 1000",
        "It's always possible to reach the end",
    ],
    [
        "Greedy BFS: expand the window of reachable positions. Each "
        "expansion is a jump.",
    ],
    "def jump(nums: list[int]) -> int:",
    """    jumps = 0
    cur_end = 0
    farthest = 0
    for i in range(len(nums) - 1):
        farthest = max(farthest, i + nums[i])
        if i == cur_end:
            jumps += 1
            cur_end = farthest
    return jumps""",
    [
        (([2, 3, 1, 1, 4],), 2),
        (([2, 3, 0, 1, 4],), 2),
    ],
    "public static int jump(int[] nums)",
    """        int jumps = 0, curEnd = 0, farthest = 0;
        for (int i = 0; i < nums.length - 1; i++) {
            farthest = Math.max(farthest, i + nums[i]);
            if (i == curEnd) { jumps++; curEnd = farthest; }
        }
        return jumps;""",
    [
        ("new int[]{2,3,1,1,4}", "2"),
        ("new int[]{2,3,0,1,4}", "2"),
    ],
    """Greedy BFS. `cur_end` is the end of the current jump's reach;
when we hit it, take another jump and extend the window.

**Time:** O(n). **Space:** O(1).
""",
)

# 4. Gas Station (Medium)
add(
    "04-gas-station", "Gas Station", "Medium",
    "There are `n` gas stations along a circular route. You have a car "
    "with an unlimited gas tank. You are given two integer arrays `gas` "
    "and `cost` of length `n`. `gas[i]` is the amount of gas at the ith "
    "station, and `cost[i]` is the amount of gas needed to travel from "
    "the ith station to the (i + 1)th. You start with an empty tank at "
    "one of the gas stations. Return the starting gas station's index if "
    "you can travel around the circuit once, otherwise return -1.",
    [
        ("gas = [1,2,3,4,5], cost = [3,4,5,1,2]", "3"),
        ("gas = [2,3,4], cost = [3,4,3]", "-1"),
    ],
    [
        "1 <= gas.length == cost.length <= 10^5",
        "0 <= gas[i], cost[i] <= 10^4",
    ],
    [
        "If total gas >= total cost, a solution exists. The starting "
        "index is the first index after which the running tank never "
        "dips below 0.",
    ],
    "def can_complete_circuit(gas: list[int], cost: list[int]) -> int:",
    """    if sum(gas) < sum(cost): return -1
    tank = 0
    start = 0
    for i in range(len(gas)):
        tank += gas[i] - cost[i]
        if tank < 0:
            start = i + 1
            tank = 0
    return start""",
    [
        (([1, 2, 3, 4, 5], [3, 4, 5, 1, 2]), 3),
        (([2, 3, 4], [3, 4, 3]), -1),
    ],
    "public static int canCompleteCircuit(int[] gas, int[] cost)",
    """        int total = 0, tank = 0, start = 0;
        for (int i = 0; i < gas.length; i++) total += gas[i] - cost[i];
        if (total < 0) return -1;
        for (int i = 0; i < gas.length; i++) {
            tank += gas[i] - cost[i];
            if (tank < 0) { start = i + 1; tank = 0; }
        }
        return start;""",
    [
        ("new int[]{1,2,3,4,5}, new int[]{3,4,5,1,2}", "3"),
        ("new int[]{2,3,4}, new int[]{3,4,3}", "-1"),
    ],
    """Greedy. If we can't make it from `i` to `i+1`, no station in
`[start, i]` can be a valid start; reset `start` to `i+1`.

**Time:** O(n). **Space:** O(1).
""",
)

# 5. Hand of Straights (Medium)
add(
    "05-hand-of-straights", "Hand of Straights", "Medium",
    "Alice has some number of cards and she wants to rearrange the cards "
    "into groups so that each group is of size `groupSize` and consists of "
    "`groupSize` consecutive cards. Given an integer array `hand` where "
    "`hand[i]` is the value written on the ith card and an integer "
    "`groupSize`, return `True` if she can rearrange the cards, or "
    "`False` otherwise.",
    [
        ("hand = [1,2,3,6,2,3,4,7,8], groupSize = 3", "True"),
        ("hand = [1,2,3,4,5], groupSize = 4", "False"),
    ],
    [
        "1 <= hand.length <= 10^4",
        "0 <= hand[i] <= 10^9",
        "1 <= groupSize <= hand.length",
    ],
    [
        "Sort the hand. For each smallest ungrouped card, try to form a "
        "group starting there.",
    ],
    "def is_n_straight_hand(hand: list[int], group_size: int) -> bool:",
    """    from collections import Counter
    if len(hand) % group_size: return False
    cnt = Counter(hand)
    for x in sorted(cnt):
        if cnt[x] == 0: continue
        need = cnt[x]
        for i in range(group_size):
            if cnt[x + i] < need:
                return False
            cnt[x + i] -= need
    return True""",
    [
        (([1, 2, 3, 6, 2, 3, 4, 7, 8], 3), True),
        (([1, 2, 3, 4, 5], 4), False),
    ],
    "public static boolean isNStraightHand(int[] hand, int groupSize)",
    """        if (hand.length % groupSize != 0) return false;
        Arrays.sort(hand);
        Map<Integer, Integer> count = new HashMap<>();
        for (int x : hand) count.merge(x, 1, Integer::sum);
        for (int x : hand) {
            int c = count.getOrDefault(x, 0);
            if (c == 0) continue;
            for (int i = 0; i < groupSize; i++) {
                int k = x + i;
                if (count.getOrDefault(k, 0) < c) return false;
                count.merge(k, -c, Integer::sum);
            }
        }
        return true;""",
    [
        ("new int[]{1,2,3,6,2,3,4,7,8}, 3", "true"),
        ("new int[]{1,2,3,4,5}, 4", "false"),
    ],
    """Greedy. Always try to form a group starting at the smallest
ungrouped card. If we can't, fail.

The Java version uses a count map and decrements instead of mutating
the array.

**Time:** O(n · groupSize). **Space:** O(n).
""",
)

# 6. Merge Triplets to Form Target (Medium)
add(
    "06-merge-triplets-to-form-target",
    "Merge Triplets to Form Target Triplet", "Medium",
    "A **triplet** is an array of three integers. You are given a 2D "
    "integer array `triplets`, where `triplets[i] = [ai, bi, ci]` "
    "describes the ith triplet. You are also given an integer array "
    "`target = [x, y, z]` that describes the triplet you want to obtain. "
    "Return `True` if it is possible to obtain the `target` triplet as "
    "an element of `triplets`, or `False` otherwise.",
    [
        ("triplets = [[2,5,3],[1,8,4],[1,7,5]], target = [2,7,5]", "True"),
        ("triplets = [[3,4,5],[4,5,6]], target = [3,2,5]", "False"),
        ("triplets = [[2,5,3],[2,5,4],[2,5,5]], target = [2,5,5]", "True"),
    ],
    [
        "1 <= triplets.length <= 10^5",
        "triplets[i].length == 3",
        "0 <= ai, bi, ci <= 1000",
        "0 <= x, y, z <= 1000",
    ],
    [
        "A triplet can contribute to the target iff each of its "
        "coordinates is <= the target's coordinate. AND the result "
        "exactly equals the target.",
    ],
    "def merge_triplets(triplets: list[list[int]], target: list[int]) -> bool:",
    """    cur = [0, 0, 0]
    for t in triplets:
        if t[0] <= target[0] and t[1] <= target[1] and t[2] <= target[2]:
            cur = [max(cur[0], t[0]), max(cur[1], t[1]), max(cur[2], t[2])]
    return cur == target""",
    [
        (([[2, 5, 3], [1, 8, 4], [1, 7, 5]], [2, 7, 5]), True),
        (([[3, 4, 5], [4, 5, 6]], [3, 2, 5]), False),
    ],
    "public static boolean mergeTriplets(int[][] triplets, int[] target)",
    """        int[] cur = new int[3];
        for (int[] t : triplets) {
            if (t[0] <= target[0] && t[1] <= target[1] && t[2] <= target[2]) {
                cur[0] = Math.max(cur[0], t[0]);
                cur[1] = Math.max(cur[1], t[1]);
                cur[2] = Math.max(cur[2], t[2]);
            }
        }
        return cur[0] == target[0] && cur[1] == target[1] && cur[2] == target[2];""",
    [
        ("new int[][]{{2,5,3},{1,8,4},{1,7,5}}, new int[]{2,7,5}", "true"),
        ("new int[][]{{3,4,5},{4,5,6}}, new int[]{3,2,5}", "false"),
    ],
    """A triplet can be merged only if each coordinate is `<= target`.
Take the max of all mergeable triplets per coordinate. If the result
equals target, return True.

**Time:** O(n). **Space:** O(1).
""",
)

# 7. Partition Labels (Medium)
add(
    "07-partition-labels", "Partition Labels", "Medium",
    "You are given a string `s`. We want to partition the string into as "
    "many parts as possible so that each letter appears in at most one "
    "part. Note that the partition is done in order — a partition is valid "
    "if and only if no letter appears in more than one part. Return a "
    "list of integers representing the size of these parts.",
    [
        ("s = 'ababcbacadefegdehijhklij'", "[9, 7, 8]"),
        ("s = 'eccbbbbdec'", "[10]"),
    ],
    [
        "1 <= len(s) <= 500",
        "s consists of lowercase English letters",
    ],
    [
        "Precompute the last occurrence of each character. Greedily "
        "extend the current partition until it includes the last "
        "occurrence of every char seen so far.",
    ],
    "def partition_labels(s: str) -> list[int]:",
    """    last = {c: i for i, c in enumerate(s)}
    out: list[int] = []
    start = end = 0
    for i, c in enumerate(s):
        end = max(end, last[c])
        if i == end:
            out.append(end - start + 1)
            start = i + 1
    return out""",
    [
        (("ababcbacadefegdehijhklij",), [9, 7, 8]),
        (("eccbbbbdec",), [10]),
    ],
    "public static List<Integer> partitionLabels(String s)",
    """        int[] last = new int[26];
        for (int i = 0; i < s.length(); i++) last[s.charAt(i) - 'a'] = i;
        List<Integer> out = new ArrayList<>();
        int start = 0, end = 0;
        for (int i = 0; i < s.length(); i++) {
            end = Math.max(end, last[s.charAt(i) - 'a']);
            if (i == end) { out.add(end - start + 1); start = i + 1; }
        }
        return out;""",
    [
        ("\"ababcbacadefegdehijhklij\"", "[9, 7, 8]"),
    ],
    """Precompute last occurrence. As we walk the string, the current
partition's end is the max of `last[c]` for chars seen. When `i ==
end`, we close the partition.

**Time:** O(n). **Space:** O(1) (26-letter alphabet).
""",
)

# 8. Valid Parenthesis String (Medium)
add(
    "08-valid-parenthesis-string", "Valid Parenthesis String", "Medium",
    "Given a string `s` containing only three types of characters: "
    "'(', ')', and '*', return `True` if `s` is **valid**. The rules: "
    "(1) any left parenthesis `'('` must have a corresponding right "
    "parenthesis `')'`. (2) any right parenthesis `')'` must have a "
    "corresponding left parenthesis `'('`. (3) left parenthesis `'('` "
    "must go before the corresponding right parenthesis `')'`. (4) `*` "
    "could be treated as a single right parenthesis `')'` or a single "
    "left parenthesis `'('` or an empty string.",
    [
        ("s = '()'", "True"),
        ("s = '(*)'", "True"),
        ("s = '(*))'", "True"),
    ],
    [
        "1 <= len(s) <= 100",
        "s consists of '(' , ')' and '*'",
    ],
    [
        "Greedy: track the range of possible open counts. `*` can be "
        "`(`, `)`, or empty.",
    ],
    "def check_valid_string(s: str) -> bool:",
    """    lo = hi = 0
    for c in s:
        if c == '(':
            lo += 1; hi += 1
        elif c == ')':
            lo = max(lo - 1, 0)
            hi -= 1
        else:  # *
            lo = max(lo - 1, 0)  # if * is ')'
            hi += 1               # if * is '('
        if hi < 0:
            return False
    return lo == 0""",
    [
        (("()",), True),
        (("(*)",), True),
        (("(*))",), True),
        (("(((*)",), False),
    ],
    "public static boolean checkValidString(String s)",
    """        int lo = 0, hi = 0;
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (c == '(') { lo++; hi++; }
            else if (c == ')') { lo = Math.max(lo - 1, 0); hi--; }
            else { lo = Math.max(lo - 1, 0); hi++; }
            if (hi < 0) return false;
        }
        return lo == 0;""",
    [
        ("\"()\"", "true"),
        ("\"(*)\"", "true"),
    ],
    """Track a range `[lo, hi]` of possible open counts after each
char. `(` adds 1, `)` removes 1 (clamped at 0), `*` is either. At the
end we need `lo == 0`.

**Time:** O(n). **Space:** O(1).
""",
)
