"""Module 10 — Backtracking problem catalog."""

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


# 1. Subsets (Medium)
add(
    "01-subsets", "Subsets", "Medium",
    "Given an integer array `nums` of unique elements, return all possible "
    "subsets (the power set). The solution set must not contain duplicate "
    "subsets. Return the subsets in any order.",
    [
        ("nums = [1,2,3]", "[[],[1],[2],[1,2],[3],[1,3],[2,3],[1,2,3]]"),
        ("nums = [0]", "[[],[0]]"),
    ],
    [
        "1 <= len(nums) <= 10",
        "-10 <= nums[i] <= 10",
        "All the numbers of nums are unique",
    ],
    [
        "For each element, choose to include it or not. Backtrack on both.",
    ],
    "def subsets(nums: list[int]) -> list[list[int]]:",
    """    out: list[list[int]] = []

    def backtrack(i: int, path: list[int]) -> None:
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
    return out""",
    [
        (([1, 2, 3],), [[], [1], [2], [1, 2], [3], [1, 3], [2, 3], [1, 2, 3]]),
    ],
    "public static List<List<Integer>> subsets(int[] nums)",
    """        List<List<Integer>> out = new ArrayList<>();
        backtrack(out, nums, 0, new ArrayList<>());
        return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] nums, int i, List<Integer> path) {
        if (i == nums.length) { out.add(new ArrayList<>(path)); return; }
        // skip nums[i]
        backtrack(out, nums, i + 1, path);
        // include nums[i]
        path.add(nums[i]);
        backtrack(out, nums, i + 1, path);
        path.remove(path.size() - 1);
    }""",
    [],
    """Two choices per element: include or skip. Total subsets = 2^n.

**Time:** O(n · 2^n). **Space:** O(n) recursion depth.
""",
)

# 2. Combination Sum (Medium)
add(
    "02-combination-sum", "Combination Sum", "Medium",
    "Given an array of **distinct** integers `candidates` and a target "
    "integer `target`, return a list of all unique combinations of "
    "`candidates` where the chosen numbers sum to `target`. The same "
    "number may be chosen from `candidates` an unlimited number of "
    "times. Two combinations are unique if the frequency of at least one "
    "of the chosen numbers is different.",
    [
        ("candidates = [2,3,6,7], target = 7", "[[2,2,3],[7]]"),
        ("candidates = [2,3,5], target = 8", "[[2,2,2,2],[2,3,3],[3,5]]"),
    ],
    [
        "1 <= candidates.length <= 30",
        "2 <= candidates[i] <= 40",
        "All elements of candidates are distinct",
        "1 <= target <= 40",
    ],
    [
        "Backtrack. At each step, try every candidate (with reuse).",
    ],
    "def combination_sum(candidates: list[int], target: int) -> list[list[int]]:",
    """    out: list[list[int]] = []

    def backtrack(i: int, path: list[int], total: int) -> None:
        if total == target:
            out.append(path.copy())
            return
        if total > target or i == len(candidates):
            return
        # skip candidates[i]
        backtrack(i + 1, path, total)
        # include candidates[i] (re-use allowed, so we stay at i)
        path.append(candidates[i])
        backtrack(i, path, total + candidates[i])
        path.pop()

    backtrack(0, [], 0)
    return out""",
    [
        (([2, 3, 6, 7], 7), [[2, 2, 3], [7]]),
        (([2, 3, 5], 8), [[2, 2, 2, 2], [2, 3, 3], [3, 5]]),
    ],
    "public static List<List<Integer>> combinationSum(int[] candidates, int target)",
    """        List<List<Integer>> out = new ArrayList<>();
        backtrack(out, candidates, 0, new ArrayList<>(), 0, target);
        return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] candidates, int i, List<Integer> path, int total, int target) {
        if (total == target) { out.add(new ArrayList<>(path)); return; }
        if (total > target || i == candidates.length) return;
        backtrack(out, candidates, i + 1, path, total, target);
        path.add(candidates[i]);
        backtrack(out, candidates, i, path, total + candidates[i], target);
        path.remove(path.size() - 1);
    }""",
    [],
    """Backtrack. At index `i`, either skip `candidates[i]` or include
it (and recurse on the same `i` to allow reuse).

**Time:** O(2^target) worst case. **Space:** O(target) recursion.
""",
)

# 3. Combination Sum II (Medium)
add(
    "03-combination-sum-ii", "Combination Sum II", "Medium",
    "Given a collection of candidate numbers (`candidates`) and a target "
    "number (`target`), find all unique combinations in `candidates` "
    "where the candidate numbers sum to `target`. Each number in "
    "`candidates` may only be used **once** in the combination. Note: "
    "The solution set must not contain duplicate combinations.",
    [
        ("candidates = [10,1,2,7,6,1,5], target = 8",
         "[[1,1,6],[1,2,5],[1,7],[2,6]]"),
        ("candidates = [2,5,2,1,2], target = 5", "[[1,2,2],[5]]"),
    ],
    [
        "1 <= candidates.length <= 100",
        "1 <= candidates[i] <= 50",
        "1 <= target <= 30",
    ],
    [
        "Sort. Skip duplicates: at the same recursion depth, if the "
        "previous element was the same value and we skipped it, skip "
        "this one too.",
    ],
    "def combination_sum2(candidates: list[int], target: int) -> list[list[int]]:",
    """    candidates = sorted(candidates)
    out: list[list[int]] = []

    def backtrack(i: int, path: list[int], total: int) -> None:
        if total == target:
            out.append(path.copy())
            return
        if total > target or i == len(candidates):
            return
        prev = -1
        for j in range(i, len(candidates)):
            if candidates[j] == prev:
                continue
            if total + candidates[j] > target:
                break
            path.append(candidates[j])
            backtrack(j + 1, path, total + candidates[j])
            path.pop()
            prev = candidates[j]

    backtrack(0, [], 0)
    return out""",
    [
        (([10, 1, 2, 7, 6, 1, 5], 8), [[1, 1, 6], [1, 2, 5], [1, 7], [2, 6]]),
        (([2, 5, 2, 1, 2], 5), [[1, 2, 2], [5]]),
    ],
    "public static List<List<Integer>> combinationSum2(int[] candidates, int target)",
    """        Arrays.sort(candidates);
        List<List<Integer>> out = new ArrayList<>();
        backtrack(out, candidates, 0, new ArrayList<>(), 0, target);
        return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] candidates, int i, List<Integer> path, int total, int target) {
        if (total == target) { out.add(new ArrayList<>(path)); return; }
        if (total > target) return;
        int prev = Integer.MIN_VALUE;
        for (int j = i; j < candidates.length; j++) {
            if (candidates[j] == prev) continue;
            if (total + candidates[j] > target) break;
            path.add(candidates[j]);
            backtrack(out, candidates, j + 1, path, total + candidates[j], target);
            path.remove(path.size() - 1);
            prev = candidates[j];
        }
    }""",
    [],
    """Sort. Loop over remaining candidates. To avoid duplicates at the
same depth, track the previous value picked (`prev`) and skip if the
current is equal.

**Time:** O(2^n). **Space:** O(n).
""",
)

# 4. Permutations (Medium)
add(
    "04-permutations", "Permutations", "Medium",
    "Given an array `nums` of distinct integers, return all the possible "
    "permutations. You may return the answer in **any order**.",
    [
        ("nums = [1,2,3]",
         "[[1,2,3],[1,3,2],[2,1,3],[2,3,1],[3,1,2],[3,2,1]]"),
        ("nums = [0,1]", "[[0,1],[1,0]]"),
    ],
    [
        "1 <= nums.length <= 6",
        "-10 <= nums[i] <= 10",
    ],
    [
        "Backtrack, swapping each unused element to the front, or use a "
        "used set.",
    ],
    "def permute(nums: list[int]) -> list[list[int]]:",
    """    out: list[list[int]] = []

    def backtrack(path: list[int], used: list[bool]) -> None:
        if len(path) == len(nums):
            out.append(path.copy())
            return
        for i in range(len(nums)):
            if used[i]:
                continue
            used[i] = True
            path.append(nums[i])
            backtrack(path, used)
            path.pop()
            used[i] = False

    backtrack([], [False] * len(nums))
    return out""",
    [
        (([1, 2, 3],), [[1, 2, 3], [1, 3, 2], [2, 1, 3], [2, 3, 1], [3, 1, 2], [3, 2, 1]]),
    ],
    "public static List<List<Integer>> permute(int[] nums)",
    """        List<List<Integer>> out = new ArrayList<>();
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
    }""",
    [],
    """Classic backtracking. At each step, try every unused element.

**Time:** O(n · n!). **Space:** O(n) recursion.
""",
)

# 5. Subsets II (Medium)
add(
    "05-subsets-ii", "Subsets II", "Medium",
    "Given an integer array `nums` that may contain duplicates, return all "
    "possible subsets (the power set). The solution set **must not** "
    "contain duplicate subsets. Return the subsets in any order.",
    [
        ("nums = [1,2,2]", "[[],[1],[1,2],[1,2,2],[2],[2,2]]"),
        ("nums = [0]", "[[],[0]]"),
    ],
    [
        "1 <= len(nums) <= 10",
        "-10 <= nums[i] <= 10",
    ],
    [
        "Sort. Skip duplicates at the same depth.",
    ],
    "def subsets_with_dup(nums: list[int]) -> list[list[int]]:",
    """    nums = sorted(nums)
    out: list[list[int]] = []

    def backtrack(i: int, path: list[int]) -> None:
        out.append(path.copy())
        for j in range(i, len(nums)):
            if j > i and nums[j] == nums[j - 1]:
                continue
            path.append(nums[j])
            backtrack(j + 1, path)
            path.pop()

    backtrack(0, [])
    return out""",
    [
        (([1, 2, 2],), [[], [1], [1, 2], [1, 2, 2], [2], [2, 2]]),
    ],
    "public static List<List<Integer>> subsetsWithDup(int[] nums)",
    """        Arrays.sort(nums);
        List<List<Integer>> out = new ArrayList<>();
        backtrack(out, nums, 0, new ArrayList<>());
        return out;
    }

    private static void backtrack(List<List<Integer>> out, int[] nums, int i, List<Integer> path) {
        out.add(new ArrayList<>(path));
        for (int j = i; j < nums.length; j++) {
            if (j > i && nums[j] == nums[j - 1]) continue;
            path.add(nums[j]);
            backtrack(out, nums, j + 1, path);
            path.remove(path.size() - 1);
        }
    }""",
    [],
    """Same as Subsets, but skip `nums[j] == nums[j-1]` at the same
recursion depth to avoid duplicates.

**Time:** O(n · 2^n). **Space:** O(n).
""",
)

# 6. Word Search (Medium)
add(
    "06-word-search", "Word Search", "Medium",
    "Given an `m x n` grid of characters `board` and a string `word`, "
    "return `True` if `word` exists in the grid. The word can be "
    "constructed from letters of sequentially adjacent cells (horizontally "
    "or vertically). The same cell may not be used more than once.",
    [
        ("board = [['A','B','C','E'],['S','F','C','S'],['A','D','E','E']], "
         "word = 'ABCCED'", "True"),
        ("board = same, word = 'ABCB'", "False"),
    ],
    [
        "m == board.length, n == board[i].length",
        "1 <= m, n <= 6",
        "1 <= word.length <= 15",
        "board and word consist of only lowercase and uppercase English letters",
    ],
    [
        "DFS from each cell. Mark visited, recurse in 4 directions, "
        "unmark on the way back.",
    ],
    "def exist(board: list[list[str]], word: str) -> bool:",
    """    rows, cols = len(board), len(board[0])

    def dfs(r: int, c: int, i: int) -> bool:
        if i == len(word):
            return True
        if r < 0 or c < 0 or r >= rows or c >= cols or board[r][c] != word[i]:
            return False
        board[r][c] = '#'   # mark
        found = (dfs(r + 1, c, i + 1) or dfs(r - 1, c, i + 1) or
                 dfs(r, c + 1, i + 1) or dfs(r, c - 1, i + 1))
        board[r][c] = word[i]   # unmark
        return found

    for r in range(rows):
        for c in range(cols):
            if dfs(r, c, 0):
                return True
    return False""",
    [
        (([["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], "ABCCED"), True),
        (([["A","B","C","E"],["S","F","C","S"],["A","D","E","E"]], "ABCB"), False),
    ],
    "public static boolean exist(char[][] board, String word)",
    """        int rows = board.length, cols = board[0].length;
        for (int r = 0; r < rows; r++) {
            for (int c = 0; c < cols; c++) {
                if (dfs(board, r, c, 0, word)) return true;
            }
        }
        return false;
    }

    private static boolean dfs(char[][] board, int r, int c, int i, String word) {
        if (i == word.length()) return true;
        if (r < 0 || c < 0 || r >= board.length || c >= board[0].length || board[r][c] != word.charAt(i)) return false;
        char saved = board[r][c];
        board[r][c] = '#';
        boolean found = dfs(board, r + 1, c, i + 1, word)
                     || dfs(board, r - 1, c, i + 1, word)
                     || dfs(board, r, c + 1, i + 1, word)
                     || dfs(board, r, c - 1, i + 1, word);
        board[r][c] = saved;
        return found;""",
    [],
    """DFS from each cell. Mark with `'#'` to avoid re-using; unmark on
the way back.

**Time:** O(m · n · 4^L) where L is the word length. **Space:** O(L).
""",
)

# 7. Palindrome Partitioning (Medium)
add(
    "07-palindrome-partitioning", "Palindrome Partitioning", "Medium",
    "Given a string `s`, partition `s` such that every substring of the "
    "partition is a palindrome. Return all possible palindrome "
    "partitionings of `s`.",
    [
        ("s = 'aab'", "[['a','a','b'],['aa','b']]"),
        ("s = 'a'", "[['a']]"),
    ],
    [
        "1 <= len(s) <= 16",
        "s contains only lowercase English letters",
    ],
    [
        "Precompute palindrome table with DP. Backtrack by trying all "
        "partitions.",
    ],
    "def partition(s: str) -> list[list[str]]:",
    """    n = len(s)
    # palindrome table
    is_pal = [[False] * n for _ in range(n)]
    for i in range(n - 1, -1, -1):
        for j in range(i, n):
            if s[i] == s[j] and (j - i < 2 or is_pal[i + 1][j - 1]):
                is_pal[i][j] = True
    out: list[list[str]] = []

    def backtrack(i: int, path: list[str]) -> None:
        if i == n:
            out.append(path.copy())
            return
        for j in range(i, n):
            if is_pal[i][j]:
                path.append(s[i:j + 1])
                backtrack(j + 1, path)
                path.pop()

    backtrack(0, [])
    return out""",
    [
        (("aab",), [["a", "a", "b"], ["aa", "b"]]),
        (("a",), [["a"]]),
    ],
    "public static List<List<String>> partition(String s)",
    """        int n = s.length();
        boolean[][] isPal = new boolean[n][n];
        for (int i = n - 1; i >= 0; i--) {
            for (int j = i; j < n; j++) {
                if (s.charAt(i) == s.charAt(j) && (j - i < 2 || isPal[i + 1][j - 1])) {
                    isPal[i][j] = true;
                }
            }
        }
        List<List<String>> out = new ArrayList<>();
        backtrack(out, isPal, s, 0, new ArrayList<>());
        return out;
    }

    private static void backtrack(List<List<String>> out, boolean[][] isPal, String s, int i, List<String> path) {
        if (i == s.length()) { out.add(new ArrayList<>(path)); return; }
        for (int j = i; j < s.length(); j++) {
            if (!isPal[i][j]) continue;
            path.add(s.substring(i, j + 1));
            backtrack(out, isPal, s, j + 1, path);
            path.remove(path.size() - 1);
        }
    }""",
    [],
    """Precompute `is_pal[i][j]` in O(n²) via DP. Then backtrack: at
position `i`, try every `j` such that `s[i..j]` is a palindrome.

**Time:** O(n · 2^n) for backtracking. **Space:** O(n²) for the table.
""",
)

# 8. Letter Combinations of a Phone Number (Medium)
add(
    "08-letter-combinations-of-a-phone-number",
    "Letter Combinations of a Phone Number", "Medium",
    "Given a string containing digits from 2-9 inclusive, return all "
    "possible letter combinations that the number could represent. Return "
    "the answer in **any order**. A mapping of digit to letters (just like "
    "on the telephone buttons) is given below. Note that 1 does not map "
    "to any letters.",
    [
        ("digits = '23'", "['ad','ae','af','bd','be','bf','cd','ce','cf']"),
        ("digits = ''", "[]"),
        ("digits = '2'", "['a','b','c']"),
    ],
    [
        "0 <= len(digits) <= 4",
        "digits[i] is a digit in the range ['2', '9']",
    ],
    [
        "Backtrack. At each digit, try all its letters.",
    ],
    "def letter_combinations(digits: str) -> list[str]:",
    """    if not digits:
        return []
    mapping = {
        '2': 'abc', '3': 'def', '4': 'ghi', '5': 'jkl',
        '6': 'mno', '7': 'pqrs', '8': 'tuv', '9': 'wxyz',
    }
    out: list[str] = []

    def backtrack(i: int, path: list[str]) -> None:
        if i == len(digits):
            out.append(''.join(path))
            return
        for c in mapping[digits[i]]:
            path.append(c)
            backtrack(i + 1, path)
            path.pop()

    backtrack(0, [])
    return out""",
    [
        (("23",), ["ad", "ae", "af", "bd", "be", "bf", "cd", "ce", "cf"]),
        (("",), []),
        (("2",), ["a", "b", "c"]),
    ],
    "public static List<String> letterCombinations(String digits)",
    """        if (digits.isEmpty()) return List.of();
        String[] map = {"abc","def","ghi","jkl","mno","pqrs","tuv","wxyz"};
        List<String> out = new ArrayList<>();
        backtrack(out, map, digits, 0, new StringBuilder());
        return out;
    }

    private static void backtrack(List<String> out, String[] map, String digits, int i, StringBuilder path) {
        if (i == digits.length()) { out.add(path.toString()); return; }
        String letters = map[digits.charAt(i) - '2'];
        for (int k = 0; k < letters.length(); k++) {
            path.append(letters.charAt(k));
            backtrack(out, map, digits, i + 1, path);
            path.deleteCharAt(path.length() - 1);
        }
    }""",
    [],
    """Backtrack. For each digit, try its letters. The empty input
returns an empty list.

**Time:** O(4^n) where n is the number of digits (4 because '7' and '9'
have 4 letters). **Space:** O(n) recursion.
""",
)

# 9. N-Queens (Hard)
add(
    "09-n-queens", "N-Queens", "Hard",
    "The n-queens puzzle is the problem of placing `n` queens on an `n x "
    "n` chessboard such that no two queens attack each other. Given an "
    "integer `n`, return all distinct solutions to the n-queens puzzle. "
    "Each solution contains a distinct board configuration of the "
    "n-queens' placement, where 'Q' and '.' both indicate a queen and "
    "an empty space respectively.",
    [
        ("n = 4", "[['.Q..','...Q','Q...','..Q.'],['..Q.','Q...','...Q','.Q..']]"),
        ("n = 1", "[['Q']]"),
    ],
    [
        "1 <= n <= 9",
    ],
    [
        "Backtrack row by row. Track attacked columns and diagonals with "
        "sets.",
    ],
    "def solve_n_queens(n: int) -> list[list[str]]:",
    """    cols: set[int] = set()
    diag1: set[int] = set()   # r - c
    diag2: set[int] = set()   # r + c
    out: list[list[str]] = []
    board: list[list[str]] = [['.'] * n for _ in range(n)]

    def backtrack(r: int) -> None:
        if r == n:
            out.append([''.join(row) for row in board])
            return
        for c in range(n):
            if c in cols or (r - c) in diag1 or (r + c) in diag2:
                continue
            board[r][c] = 'Q'
            cols.add(c); diag1.add(r - c); diag2.add(r + c)
            backtrack(r + 1)
            board[r][c] = '.'
            cols.remove(c); diag1.remove(r - c); diag2.remove(r + c)

    backtrack(0)
    return out""",
    [
        ((4,), [[".Q..","...Q","Q...","..Q."], ["..Q.","Q...","...Q",".Q.."]]),
        ((1,), [["Q"]]),
    ],
    "public static List<List<String>> solveNQueens(int n)",
    """        Set<Integer> cols = new HashSet<>();
        Set<Integer> diag1 = new HashSet<>();   // r - c
        Set<Integer> diag2 = new HashSet<>();   // r + c
        char[][] board = new char[n][n];
        for (char[] row : board) Arrays.fill(row, '.');
        List<List<String>> out = new ArrayList<>();
        backtrack(out, board, cols, diag1, diag2, 0, n);
        return out;
    }

    private static void backtrack(List<List<String>> out, char[][] board, Set<Integer> cols, Set<Integer> diag1, Set<Integer> diag2, int r, int n) {
        if (r == n) {
            List<String> sol = new ArrayList<>();
            for (char[] row : board) sol.add(new String(row));
            out.add(sol);
            return;
        }
        for (int c = 0; c < n; c++) {
            if (cols.contains(c) || diag1.contains(r - c) || diag2.contains(r + c)) continue;
            board[r][c] = 'Q';
            cols.add(c); diag1.add(r - c); diag2.add(r + c);
            backtrack(out, board, cols, diag1, diag2, r + 1, n);
            board[r][c] = '.';
            cols.remove(c); diag1.remove(r - c); diag2.remove(r + c);
        }
    }""",
    [],
    """Place queens row by row. For each column, check it's not under
attack (no queen in the same column or either diagonal). Three sets —
columns, `r - c`, `r + c` — give O(1) attack checks.

**Time:** O(n!) worst case, much less in practice. **Space:** O(n) for
the sets + board.
""",
)
