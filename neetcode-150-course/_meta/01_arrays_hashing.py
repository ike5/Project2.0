"""Module 01 — Arrays & Hashing problem catalog.

Each problem entry is a dict with:
    slug, name, difficulty, brief, examples, constraints, hints,
    py_sig,    py_body,    py_tests,
    java_sig,  java_body,  java_tests,
    walkthrough (str)

- py_sig is the *full* Python function signature, e.g.
    "def two_sum(nums: list[int], target: int) -> list[int]:"
  The body of the function comes from py_body (which must be indented).
- py_tests is a list of tuples ((args...), expected). The expected value is
  rendered with repr() and compared to the function return value.
- java_sig is the Java method signature, e.g.
    "public static int[] twoSum(int[] nums, int target)"
- java_body is the body of that method (indented by 8 spaces for placement).
- java_tests is a list of ((args...), expected), where args are Java literal
  expressions. They're rendered as "Solution.<name>(args)".

The generator wraps everything into runnable files.
"""

PROBLEMS = []


def add(slug, name, difficulty, brief, examples, constraints, hints,
        py_sig, py_body, py_tests, java_sig, java_body, java_tests,
        walkthrough):
    PROBLEMS.append({
        "slug": slug,
        "name": name,
        "difficulty": difficulty,
        "brief": brief,
        "examples": examples,
        "constraints": constraints,
        "hints": hints,
        "py_sig": py_sig,
        "py_body": py_body,
        "py_tests": py_tests,
        "java_sig": java_sig,
        "java_body": java_body,
        "java_tests": java_tests,
        "walkthrough": walkthrough,
    })


# ----- 1. Contains Duplicate -------------------------------------------------
add(
    "01-contains-duplicate", "Contains Duplicate", "Easy",
    "Given an integer array `nums`, return `True` if any value appears at "
    "least twice. Return `False` if every element is distinct.",
    [
        ("nums = [1, 2, 3, 1]", "True"),
        ("nums = [1, 2, 3, 4]", "False"),
        ("nums = [1, 1, 1, 3, 3, 4, 3, 2, 4, 2]", "True"),
    ],
    [
        "1 <= len(nums) <= 10^5",
        "-10^9 <= nums[i] <= 10^9",
    ],
    [
        "What structure gives O(1) membership checks?",
        "You don't need to count occurrences — one duplicate is enough.",
    ],
    "def contains_duplicate(nums: list[int]) -> bool:",
    """    seen: set[int] = set()
    for x in nums:
        if x in seen:
            return True
        seen.add(x)
    return False""",
    [
        (([1, 2, 3, 1],), True),
        (([1, 2, 3, 4],), False),
        (([1, 1, 1, 3, 3, 4, 3, 2, 4, 2],), True),
        (([],), False),
    ],
    "public static boolean containsDuplicate(int[] nums)",
    """        Set<Integer> seen = new HashSet<>();
        for (int x : nums) {
            if (!seen.add(x)) return true;
        }
        return false""",
    [
        ("new int[]{1, 2, 3, 1}", "true"),
        ("new int[]{1, 2, 3, 4}", "false"),
        ("new int[]{1, 1, 1, 3, 3, 4, 3, 2, 4, 2}", "true"),
        ("new int[]{}", "false"),
    ],
    """## Intuition
We only need to detect *one* duplicate, so we don't need to count. A hash set
gives O(1) membership checks.

## Approach
Walk the array. If the current value is already in the set, return True.
Otherwise, add it. If we finish the loop, every element was unique.

## Complexity
- **Time:** O(n) — one pass; each set op is amortized O(1).
- **Space:** O(n) worst case (no duplicates).

## Follow-ups
- *What if the array is sorted?* Then a one-pass O(1)-space check works: any
  `nums[i] == nums[i+1]` is a duplicate.
- *What if memory is the bottleneck?* Sort the array in place (O(1) extra
  bytes if you count the input's own space) and then check adjacent pairs.
- *What if duplicates are *allowed* but you want to know the count?* Use a
  `Counter` / `Map<K,Integer>` instead of a set.
""",
)


# ----- 2. Valid Anagram ------------------------------------------------------
add(
    "02-valid-anagram", "Valid Anagram", "Easy",
    "Given two strings `s` and `t`, return `True` iff `t` is an anagram of "
    "`s` (same characters, same multiplicities).",
    [
        ("s = 'anagram', t = 'nagaram'", "True"),
        ("s = 'rat', t = 'car'", "False"),
    ],
    [
        "1 <= len(s), len(t) <= 5 * 10^4",
        "Strings consist of lowercase English letters",
    ],
    [
        "Two strings are anagrams iff they have the same character counts.",
        "`collections.Counter` does the work in one line. In Java, an "
        "`int[26]` is fastest.",
    ],
    "def is_anagram(s: str, t: str) -> bool:",
    """    from collections import Counter
    return Counter(s) == Counter(t)""",
    [
        (("anagram", "nagaram"), True),
        (("rat", "car"), False),
        (("a", "a"), True),
        (("ab", "a"), False),
        (("", ""), True),
    ],
    "public static boolean isAnagram(String s, String t)",
    """        if (s.length() != t.length()) return false;
        int[] count = new int[26];
        for (int i = 0; i < s.length(); i++) {
            count[s.charAt(i) - 'a']++;
            count[t.charAt(i) - 'a']--;
        }
        for (int c : count) if (c != 0) return false;
        return true""",
    [
        ("\"anagram\", \"nagaram\"", "true"),
        ("\"rat\", \"car\"", "false"),
        ("\"a\", \"a\"", "true"),
        ("\"ab\", \"a\"", "false"),
        ("\"\", \"\"", "true"),
    ],
    """## Intuition
Anagrams have identical character counts, so we just compare counts.

## Approach
Two equivalent options:
1. **Sort both strings** and compare — O(n log n), O(1) extra.
2. **Count** characters in a fixed-size array (`int[26]` for lowercase
   letters) — O(n), O(1) extra.

We use the count version. We don't even need a separate `int[26]` for `t`:
increment for `s`, decrement for `t`, then check that all buckets are 0.

## Complexity
- **Time:** O(n) — one pass over both strings.
- **Space:** O(1) — the count array has size 26 regardless of input.

## Follow-ups
- *Unicode input?* `int[26]` no longer works. Use a `Map<Character,Integer>`.
- *Very long strings?* Both algorithms are linear-ish; consider memory-mapping
  the file. (Outside the scope of interviews.)
- *Streaming input?* Maintain the running count and emit "still an anagram so
  far" as long as no count goes negative.
""",
)


# ----- 3. Two Sum ------------------------------------------------------------
add(
    "03-two-sum", "Two Sum", "Easy",
    "Given an array `nums` and an integer `target`, return the **indices** "
    "of the two numbers such that they add up to `target`. Exactly one "
    "solution exists. You may not use the same element twice.",
    [
        ("nums = [2,7,11,15], target = 9", "[0, 1]"),
        ("nums = [3,2,4],    target = 6", "[1, 2]"),
        ("nums = [3,3],      target = 6", "[0, 1]"),
    ],
    [
        "2 <= len(nums) <= 10^4",
        "-10^9 <= nums[i] <= 10^9",
        "Exactly one valid answer",
    ],
    [
        "Brute force is O(n²). Can you do it in one pass?",
        "For each `x`, ask: have I seen `target - x`?",
    ],
    "def two_sum(nums: list[int], target: int) -> list[int]:",
    """    seen: dict[int, int] = {}   # value -> index
    for i, x in enumerate(nums):
        if target - x in seen:
            return [seen[target - x], i]
        seen[x] = i
    return []""",
    [
        (([2, 7, 11, 15], 9), [0, 1]),
        (([3, 2, 4], 6), [1, 2]),
        (([3, 3], 6), [0, 1]),
        (([-1, -2, -3, -4, -5], -8), [2, 4]),
    ],
    "public static int[] twoSum(int[] nums, int target)",
    """        Map<Integer, Integer> seen = new HashMap<>();
        for (int i = 0; i < nums.length; i++) {
            int need = target - nums[i];
            if (seen.containsKey(need)) {
                return new int[] { seen.get(need), i };
            }
            seen.put(nums[i], i);
        }
        return new int[] {}""",
    [
        ("new int[]{2, 7, 11, 15}, 9", "[0, 1]"),
        ("new int[]{3, 2, 4}, 6", "[1, 2]"),
        ("new int[]{3, 3}, 6", "[0, 1]"),
    ],
    """## Intuition
For each `x`, the *complement* `target - x` must have appeared earlier. We can
check this in O(1) with a hash map from value to its index.

## Approach
Walk the array. Before inserting `x` at index `i`, check whether
`target - x` is in the map. If yes, we have our pair.

## Complexity
- **Time:** O(n) — one pass; each map op is amortized O(1).
- **Space:** O(n) worst case (no match until the end).

## Follow-ups
- *Return the values, not the indices?* Drop the index from the map.
- *Sorted input, return values in order?* Use the two-pointer technique
  (Module 02) — O(1) extra space, but O(n) time.
- *What if there are multiple valid pairs?* Keep going; collect all pairs.
""",
)


# ----- 4. Group Anagrams -----------------------------------------------------
add(
    "04-group-anagrams", "Group Anagrams", "Medium",
    "Given an array of strings `strs`, group the anagrams together. You "
    "may return the groups in any order.",
    [
        ("strs = ['eat','tea','tan','ate','nat','bat']",
         "[['bat'],['nat','tan'],['ate','eat','tea']]"),
        ("strs = ['']", "[['']]"),
        ("strs = ['a']", "[['a']]"),
    ],
    [
        "1 <= len(strs) <= 10^4",
        "0 <= len(strs[i]) <= 100",
        "strs[i] consists of lowercase English letters",
    ],
    [
        "Anagrams share the same sorted form (or the same character-count "
        "tuple).",
        "Use the sorted form (or count tuple) as the map key.",
    ],
    "def group_anagrams(strs: list[str]) -> list[list[str]]:",
    """    from collections import defaultdict
    groups: dict[tuple[str, ...], list[str]] = defaultdict(list)
    for s in strs:
        key = tuple(sorted(s))
        groups[key].append(s)
    return list(groups.values())""",
    [
        ((["eat", "tea", "tan", "ate", "nat", "bat"],),
         [["bat"], ["nat", "tan"], ["ate", "eat", "tea"]]),
        (([""],), [[""]]),
        ((["a"],), [["a"]]),
    ],
    "public static List<List<String>> groupAnagrams(String[] strs)",
    """        Map<String, List<String>> groups = new HashMap<>();
        for (String s : strs) {
            char[] chars = s.toCharArray();
            Arrays.sort(chars);
            String key = new String(chars);
            groups.computeIfAbsent(key, k -> new ArrayList<>()).add(s);
        }
        return new ArrayList<>(groups.values())""",
    [
        ("new String[]{\"eat\",\"tea\",\"tan\",\"ate\",\"nat\",\"bat\"}",
         "[[bat], [nat, tan], [ate, eat, tea]]"),
        ("new String[]{ \"\" }", "[[\"\"]]"),
        ("new String[]{\"a\"}", "[[a]]"),
    ],
    """## Intuition
Anagrams become identical once sorted. So they share a *canonical form* (the
sorted string). Group by that.

## Approach
For each string, sort its characters to produce a key. Insert the string into
the bucket keyed by that key.

## Complexity
- **Time:** O(n · k log k) — n strings of average length k, each sorted in
  O(k log k).
- **Space:** O(n · k) — the buckets store all strings.

### Faster key (count-tuple)
A common optimization is to use the **character-count tuple** as the key,
e.g. `(2, 0, 0, ..., 1)` for `"aac...d"`. This drops the sort to O(k).

## Follow-ups
- *Streaming input?* Group as they come in; you don't need the full list.
- *Memory-constrained?* Sort each string in place to produce the key, but
  you'll need to keep the original. Hash a signature like `MD5(sorted)`.
""",
)


# ----- 5. Top K Frequent Elements --------------------------------------------
add(
    "05-top-k-frequent-elements", "Top K Frequent Elements", "Medium",
    "Given an integer array `nums` and an integer `k`, return the `k` most "
    "frequent elements. You may return the answer in any order.",
    [
        ("nums = [1,1,1,2,2,3], k = 2", "[1, 2]"),
        ("nums = [1], k = 1", "[1]"),
    ],
    [
        "1 <= nums.length <= 10^5",
        "k is in the range [1, the number of unique elements]",
    ],
    [
        "Approach 1: a min-heap of size k — O(n log k).",
        "Approach 2 (bucket sort): the max frequency is at most n. Make a "
        "list of buckets indexed by frequency, then walk down.",
    ],
    "def top_k_frequent(nums: list[int], k: int) -> list[int]:",
    """    from collections import Counter
    import heapq
    count = Counter(nums)
    return [x for x, _ in heapq.nlargest(k, count.items(), key=lambda p: p[1])]""",
    [
        (([1, 1, 1, 2, 2, 3], 2), [1, 2]),
        (([1], 1), [1]),
        (([1, 2, 3, 4, 5], 5), [1, 2, 3, 4, 5]),
        (([4, 1, -1, 2, -1, 2, 3], 2), [-1, 2]),
    ],
    "public static List<Integer> topKFrequent(int[] nums, int k)",
    """        Map<Integer, Integer> count = new HashMap<>();
        for (int x : nums) count.merge(x, 1, Integer::sum);
        // bucket sort by frequency; max freq is nums.length
        List<Integer>[] buckets = new List[nums.length + 1];
        for (int i = 0; i < buckets.length; i++) buckets[i] = new ArrayList<>();
        for (var e : count.entrySet()) buckets[e.getValue()].add(e.getKey());
        List<Integer> out = new ArrayList<>();
        for (int f = buckets.length - 1; f >= 0 && out.size() < k; f--) {
            out.addAll(buckets[f]);
        }
        return out""",
    [
        ("new int[]{1,1,1,2,2,3}, 2", "[1, 2]"),
        ("new int[]{1}, 1", "[1]"),
    ],
    """## Intuition
Count everything, then pick the top k. The classic "top-k" problem.

## Approach
We use **bucket sort by frequency**. The max frequency is at most `n`, so we
make a list of `n+1` buckets where `buckets[f]` holds all values with
frequency `f`. Walk from the highest frequency down and take `k` values.

## Complexity
- **Time:** O(n) — counting, bucketing, and walking down are all linear.
- **Space:** O(n) — the count map and the buckets.

## Alternative: min-heap of size k
Maintain a heap of size k, push `(frequency, value)`, pop the smallest when
the heap grows past k. O(n log k) time, O(k) space. Use this if `k` is much
smaller than `n` and the value range is huge.

## Follow-ups
- *In O(k log k) total?* Quickselect on `(frequency, value)` pairs.
- *Streaming values?* Count-Sketch / Misra-Gries for approximate top-k.
""",
)


# ----- 6. Product of Array Except Self --------------------------------------
add(
    "06-product-of-array-except-self", "Product of Array Except Self", "Medium",
    "Given an integer array `nums`, return an array `answer` such that "
    "`answer[i]` equals the product of all the elements of `nums` except "
    "`nums[i]`. Solve it in O(n) time without using the division operator.",
    [
        ("nums = [1,2,3,4]", "[24,12,8,6]"),
        ("nums = [-1,1,0,-3,3]", "[0,0,9,0,0]"),
    ],
    [
        "2 <= len(nums) <= 10^5",
        "-30 <= nums[i] <= 30",
        "The product of any prefix or suffix fits in a 32-bit int",
    ],
    [
        "Compute prefix products and suffix products in two passes.",
        "You can do it in O(1) extra space by reusing `answer` for the prefix "
        "and a running suffix variable.",
    ],
    "def product_except_self(nums: list[int]) -> list[int]:",
    """    n = len(nums)
    answer = [1] * n
    # prefix products: answer[i] = product of nums[0..i-1]
    p = 1
    for i in range(n):
        answer[i] = p
        p *= nums[i]
    # suffix products: multiply by product of nums[i+1..n-1]
    s = 1
    for i in range(n - 1, -1, -1):
        answer[i] *= s
        s *= nums[i]
    return answer""",
    [
        (([1, 2, 3, 4],), [24, 12, 8, 6]),
        (([-1, 1, 0, -3, 3],), [0, 0, 9, 0, 0]),
        (([2, 3],), [3, 2]),
    ],
    "public static int[] productExceptSelf(int[] nums)",
    """        int n = nums.length;
        int[] answer = new int[n];
        int p = 1;
        for (int i = 0; i < n; i++) { answer[i] = p; p *= nums[i]; }
        int s = 1;
        for (int i = n - 1; i >= 0; i--) { answer[i] *= s; s *= nums[i]; }
        return answer""",
    [
        ("new int[]{1,2,3,4}", "[24, 12, 8, 6]"),
        ("new int[]{-1,1,0,-3,3}", "[0, 0, 9, 0, 0]"),
        ("new int[]{2, 3}", "[3, 2]"),
    ],
    """## Intuition
For each `i`, the answer is `(product of all elements to the left) * (product
of all elements to the right)`.

## Approach
Two passes, O(1) extra space (the output array counts as output).
1. **Forward pass**: fill `answer[i]` with the product of `nums[0..i-1]`.
2. **Backward pass**: maintain a running suffix product and multiply it into
   `answer[i]`.

## Complexity
- **Time:** O(n).
- **Space:** O(1) extra (the output doesn't count).

## Follow-ups
- *What if the input can have zeros and the problem allowed division?*
  Compute the total product, divide by each `nums[i]`, but replace the
  result with 0 for any `nums[i] == 0`. Handle multiple zeros: every
  answer is 0.
- *64-bit values?* Use `long` in Java or check constraints.
""",
)


# ----- 7. Valid Sudoku -------------------------------------------------------
add(
    "07-valid-sudoku", "Valid Sudoku", "Medium",
    "Determine if a 9x9 Sudoku board is valid. Only the filled cells need "
    "to be validated: each row, each column, and each of the nine 3x3 "
    "sub-boxes must contain the digits 1-9 without repetition.",
    [
        ("A standard 9x9 valid board", "True"),
        ("A standard 9x9 board with one duplicate in a sub-box", "False"),
    ],
    [
        "board.length == 9, board[i].length == 9",
        "board[i][j] is a digit '1'-'9' or '.'",
    ],
    [
        "Validate rows, columns, and 3x3 boxes separately.",
        "You can do all three in one pass with three sets per row/col/box "
        "— or one pass with a single set per (row, col, box) triple.",
    ],
    "def is_valid_sudoku(board: list[list[str]]) -> bool:",
    """    rows: list[set[str]] = [set() for _ in range(9)]
    cols: list[set[str]] = [set() for _ in range(9)]
    boxes: list[set[str]] = [set() for _ in range(9)]
    for r in range(9):
        for c in range(9):
            v = board[r][c]
            if v == '.':
                continue
            b = (r // 3) * 3 + (c // 3)
            if v in rows[r] or v in cols[c] or v in boxes[b]:
                return False
            rows[r].add(v)
            cols[c].add(v)
            boxes[b].add(v)
    return True""",
    [
        # A valid board
        (([["5","3",".",".","7",".",".",".","."],
           ["6",".",".","1","9","5",".",".","."],
           [".","9","8",".",".",".",".","6","."],
           ["8",".",".",".","6",".",".",".","3"],
           ["4",".",".","8",".","3",".",".","1"],
           ["7",".",".",".","2",".",".",".","6"],
           [".","6",".",".",".",".","2","8","."],
           [".",".",".","4","1","9",".",".","5"],
           [".",".",".",".","8",".",".","7","9"]],
          ), True),
        # A board with a duplicate in a column
        (([["8","3",".",".","7",".",".",".","."],
           ["6",".",".","1","9","5",".",".","."],
           [".","9","8",".",".",".",".","6","."],
           ["8",".",".",".","6",".",".",".","3"],
           ["4",".",".","8",".","3",".",".","1"],
           ["7",".",".",".","2",".",".",".","6"],
           [".","6",".",".",".",".","2","8","."],
           [".",".",".","4","1","9",".",".","5"],
           [".",".",".",".","8",".",".","7","9"]],
          ), False),
    ],
    "public static boolean isValidSudoku(char[][] board)",
    """        Set<Character>[] rows = new Set[9];
        Set<Character>[] cols = new Set[9];
        Set<Character>[] boxes = new Set[9];
        for (int i = 0; i < 9; i++) {
            rows[i] = new HashSet<>();
            cols[i] = new HashSet<>();
            boxes[i] = new HashSet<>();
        }
        for (int r = 0; r < 9; r++) {
            for (int c = 0; c < 9; c++) {
                char v = board[r][c];
                if (v == '.') continue;
                int b = (r / 3) * 3 + (c / 3);
                if (!rows[r].add(v) || !cols[c].add(v) || !boxes[b].add(v)) {
                    return false;
                }
            }
        }
        return true""",
    [],
    """## Intuition
The board is 9x9. The 3x3 sub-box index for cell `(r, c)` is
`(r // 3) * 3 + (c // 3)`. We track what we've seen in each row, each
column, and each sub-box.

## Approach
Three sets per dimension. For each filled cell, check that its digit is
absent from all three. (Or use the trick that `Set.add` returns `false` on
duplicate, as in the Java version above.)

## Complexity
- **Time:** O(81) = O(1) — board is fixed-size.
- **Space:** O(81) = O(1) — three sets of up to 9 elements each.

## Follow-ups
- *What if the board is N x N and boxes are √N x √N?* Same approach, with
  `int sqrtN = (int) Math.sqrt(N)`.
- *Solve the sudoku (place the empty cells)?* Backtracking — Module 10.
""",
)


# ----- 8. Encode and Decode Strings ------------------------------------------
add(
    "08-encode-and-decode-strings", "Encode and Decode Strings", "Medium",
    "Design an algorithm to encode a list of strings into a single string. "
    "The encoded string is then decoded back to the original list of strings. "
    "The encoding must handle strings containing any characters, including "
    "the delimiter.",
    [
        ("['hello','world']", "['hello','world']"),
        ("['', '']", "['', '']"),
        ("['a#b', 'c']", "['a#b', 'c']"),
    ],
    [
        "0 <= len(strs) <= 200",
        "0 <= len(strs[i]) <= 200",
        "Strings may contain any ASCII characters",
    ],
    [
        "Length-prefix the encoding: store `<len>#<s>` for each string.",
        "Walk the encoded string and read until '#' to find each length.",
    ],
    "def encode(strs: list[str]) -> str:",
    """    return ''.join(f"{len(s)}#{s}" for s in strs)""",
    [
        ((["hello", "world"],), "5#hello5#world"),
        ((["", ""],), "0#0#"),
        ((["a#b", "c"],), "3#a#b1#c"),
    ],
    "public static String encode(List<String> strs)",
    """        StringBuilder sb = new StringBuilder();
        for (String s : strs) sb.append(s.length()).append('#').append(s);
        return sb.toString()""",
    [],
    """## Intuition
We need a delimiter that **cannot appear in the data**. If we *length-prefix*
each string, the delimiter can be anything (we never need to look for it in
the data).

## Approach
Encoder: for each `s`, append `len(s) + '#' + s`.
Decoder: read digits until '#' to learn the length, then read exactly that
many characters.

## Complexity
- **Time:** O(n) where n is the total length of all strings.
- **Space:** O(n) for the output.

## Why not a non-printable delimiter?
A non-printable character (e.g. `\\u0001`) *does* work in some contexts, but
the input strings may legally contain *any* character. Length-prefixing is
robust.

## Follow-ups
- *Streaming decode?* Stateful — you need to know when one string ends and
  the next begins. The length-prefix approach streams cleanly: read length,
  read that many bytes.
""",
)


# ----- 9. Longest Consecutive Sequence --------------------------------------
add(
    "09-longest-consecutive-sequence", "Longest Consecutive Sequence", "Medium",
    "Given an unsorted array of integers `nums`, return the length of the "
    "longest sequence of consecutive elements. The algorithm must run in "
    "O(n) time.",
    [
        ("nums = [100,4,200,1,3,2]", "4"),  # [1, 2, 3, 4]
        ("nums = [0,3,7,2,5,8,4,6,0,1]", "9"),
        ("nums = []", "0"),
    ],
    [
        "0 <= nums.length <= 10^5",
        "-10^9 <= nums[i] <= 10^9",
    ],
    [
        "Sort then walk — O(n log n). We can do better with a set.",
        "For each x, only start counting if x-1 is NOT in the set (i.e. x "
        "is the start of a run). Then walk x+1, x+2, ...",
    ],
    "def longest_consecutive(nums: list[int]) -> int:",
    """    s = set(nums)
    best = 0
    for x in s:
        if x - 1 in s:
            continue  # x is not the start of a run
        length = 1
        while x + length in s:
            length += 1
        best = max(best, length)
    return best""",
    [
        (([100, 4, 200, 1, 3, 2],), 4),
        (([0, 3, 7, 2, 5, 8, 4, 6, 0, 1],), 9),
        (([],), 0),
        (([1, 2, 0, 1],), 3),
    ],
    "public static int longestConsecutive(int[] nums)",
    """        Set<Integer> s = new HashSet<>();
        for (int x : nums) s.add(x);
        int best = 0;
        for (int x : s) {
            if (s.contains(x - 1)) continue;
            int length = 1;
            while (s.contains(x + length)) length++;
            best = Math.max(best, length);
        }
        return best""",
    [
        ("new int[]{100,4,200,1,3,2}", "4"),
        ("new int[]{0,3,7,2,5,8,4,6,0,1}", "9"),
        ("new int[]{}", "0"),
    ],
    """## Intuition
For each `x`, ask: is `x-1` also in the array? If **no**, then `x` is the
*start* of a run, and we walk forward counting how long the run is.

This guarantees each element is visited at most twice (once as the outer
loop, at most once as `x + length` for some other start), so the total work
is O(n).

## Approach
1. Put everything in a set.
2. For each `x` in the set:
   - If `x - 1` is in the set, skip — we don't want to start in the middle.
   - Otherwise, walk `x + 1, x + 2, ...` while present, counting.
3. Return the longest count.

## Complexity
- **Time:** O(n) — each element is checked O(1) times in the outer loop and
  O(1) times in the inner walk (since it can only be `x + length` for a
  single start).
- **Space:** O(n) for the set.

## Follow-ups
- *What if you can sort?* Sort in O(n log n), then walk adjacent pairs.
  Easier to code, but slower.
- *Streaming input?* Maintain a `Map<Integer, Integer>` of "run length ending
  at x" using Union-Find-like merging. (Module 11.)
""",
)
