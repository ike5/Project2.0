"""Module 04 — Stack problem catalog."""

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


# 1. Valid Parentheses (Easy)
add(
    "01-valid-parentheses", "Valid Parentheses", "Easy",
    "Given a string `s` containing just the characters '()[]{}', determine "
    "if the input string is valid. Brackets must be closed in the correct "
    "order, and every open bracket must be matched by a close bracket of "
    "the same type.",
    [
        ("s = '()[]{}'", "True"),
        ("s = '(]'", "False"),
        ("s = '([)]'", "False"),
        ("s = '{[]}'", "True"),
    ],
    [
        "1 <= len(s) <= 10^4",
        "s consists of parentheses only",
    ],
    [
        "Push opening brackets; on a closing bracket, the top of the stack "
        "must be the matching opener.",
        "At the end the stack must be empty.",
    ],
    "def is_valid(s: str) -> bool:",
    """    pairs = {')': '(', ']': '[', '}': '{'}
    stack: list[str] = []
    for c in s:
        if c in pairs:
            if not stack or stack[-1] != pairs[c]:
                return False
            stack.pop()
        else:
            stack.append(c)
    return not stack""",
    [
        (("()[]{}",), True),
        (("(]",), False),
        (("([)]",), False),
        (("{[]}",), True),
        (("",), True),
    ],
    "public static boolean isValid(String s)",
    """        Map<Character, Character> pairs = Map.of(
            ')', '(', ']', '[', '}', '{'
        );
        Deque<Character> stack = new ArrayDeque<>();
        for (int i = 0; i < s.length(); i++) {
            char c = s.charAt(i);
            if (pairs.containsKey(c)) {
                if (stack.isEmpty() || stack.peek() != pairs.get(c)) return false;
                stack.pop();
            } else {
                stack.push(c);
            }
        }
        return stack.isEmpty()""",
    [
        ("\"()[]{}\"", "true"),
        ("\"(]\"", "false"),
        ("\"([)]\"", "false"),
        ("\"{[]}\"", "true"),
    ],
    """Push openers. On a closer, the stack top must be the matching opener
(else invalid). At the end, the stack must be empty.

**Time:** O(n). **Space:** O(n).
""",
)

# 2. Min Stack (Medium)
add(
    "02-min-stack", "Min Stack", "Medium",
    "Design a stack that supports push, pop, top, and retrieving the "
    "minimum element in constant time. Implement the `MinStack` class with "
    "`push(x)`, `pop()`, `top()`, and `get_min()` methods.",
    [
        ("MinStack(); push(-2); push(0); push(-3); get_min() -> -3; pop(); top() -> 0; get_min() -> -2",
         "[-3, 0, -2]"),
    ],
    [
        "-2^31 <= x <= 2^31 - 1",
        "Methods must run in O(1) time",
        "Up to 3 * 10^4 calls",
    ],
    [
        "Two-stack approach: one for values, one for the running min.",
        "Single-stack approach: store (value, min-so-far) tuples.",
    ],
    "class MinStack:",
    """    def __init__(self) -> None:
        self._data: list[int] = []
        self._mins: list[int] = []

    def push(self, x: int) -> None:
        self._data.append(x)
        if not self._mins or x <= self._mins[-1]:
            self._mins.append(x)

    def pop(self) -> None:
        x = self._data.pop()
        if x == self._mins[-1]:
            self._mins.pop()

    def top(self) -> int:
        return self._data[-1]

    def get_min(self) -> int:
        return self._mins[-1]""",
    [
        # Functional-style test: build, push, query, pop, query
        (("__init__",), None),
    ],
    # Java: we expose a public static MinStack in the file, but it's a stateful
    # class — we test it imperatively in main().
    "public static class MinStack",
    """        private final Deque<int[]> stack = new ArrayDeque<>();
        public void push(int x) {
            int min = stack.isEmpty() ? x : Math.min(x, stack.peek()[1]);
            stack.push(new int[] { x, min });
        }
        public void pop() { stack.pop(); }
        public int top() { return stack.peek()[0]; }
        public int getMin() { return stack.peek()[1]; }""",
    [],
    """Two natural approaches:

- **Two stacks** (values, running mins).
- **One stack of (value, min-so-far) pairs** (the Java version above).

Both give O(1) per operation. The pair version is slightly more compact.

**Time:** O(1) per op. **Space:** O(n).
""",
)

# 3. Evaluate Reverse Polish Notation (Medium)
add(
    "03-evaluate-reverse-polish-notation",
    "Evaluate Reverse Polish Notation", "Medium",
    "Evaluate the value of an arithmetic expression in Reverse Polish "
    "Notation. Valid operators are `+`, `-`, `*`, `/`. Each operand may be "
    "an integer or another expression. Division between two integers should "
    "**truncate toward zero**.",
    [
        ("tokens = ['2','1','+','3','*']", "9"),  # (2+1)*3
        ("tokens = ['4','13','5','/','+']", "6"),  # 4 + 13/5 = 4 + 2
        ("tokens = ['10','6','9','3','+','-11','*','/','*','17','+','5','+']",
         "22"),
    ],
    [
        "1 <= len(tokens) <= 10^4",
        "tokens[i] is either an integer in [-200, 200] or one of '+-*/'",
        "The expression is always valid and divides by zero never occurs",
    ],
    [
        "Push numbers; on an operator, pop two, compute, push the result.",
        "Order matters: for `a - b` and `a / b`, the first popped is `b`.",
    ],
    "def eval_rpn(tokens: list[str]) -> int:",
    """    stack: list[int] = []
    ops = {
        '+': lambda a, b: a + b,
        '-': lambda a, b: a - b,
        '*': lambda a, b: a * b,
        '/': lambda a, b: int(a / b),  # truncate toward zero
    }
    for t in tokens:
        if t in ops:
            b = stack.pop()
            a = stack.pop()
            stack.append(ops[t](a, b))
        else:
            stack.append(int(t))
    return stack[-1]""",
    [
        ((["2", "1", "+", "3", "*"],), 9),
        ((["4", "13", "5", "/", "+"],), 6),
        ((["10", "6", "9", "3", "+", "-11", "*", "/", "*", "17", "+", "5", "+"],), 22),
    ],
    "public static int evalRPN(String[] tokens)",
    """        Deque<Integer> stack = new ArrayDeque<>();
        for (String t : tokens) {
            switch (t) {
                case "+" -> { int b = stack.pop(); int a = stack.pop(); stack.push(a + b); }
                case "-" -> { int b = stack.pop(); int a = stack.pop(); stack.push(a - b); }
                case "*" -> { int b = stack.pop(); int a = stack.pop(); stack.push(a * b); }
                case "/" -> { int b = stack.pop(); int a = stack.pop(); stack.push(a / b); }
                default  -> stack.push(Integer.parseInt(t));
            }
        }
        return stack.pop()""",
    [
        ("new String[]{\"2\",\"1\",\"+\",\"3\",\"*\"}", "9"),
        ("new String[]{\"4\",\"13\",\"5\",\"/\",\"+\"}", "6"),
    ],
    """Stack-based. Numbers push. Operators pop the top two, compute, push
the result. Watch the order: for `a - b` and `a / b`, the second-popped is
`b`. In Java, `int / int` already truncates toward zero, so no special
handling. In Python, `int(a / b)` (not `a // b`) is required to match
the problem's contract for negative results.

**Time:** O(n). **Space:** O(n).
""",
)

# 4. Generate Parentheses (Medium)
add(
    "04-generate-parentheses", "Generate Parentheses", "Medium",
    "Given `n` pairs of parentheses, write a function to generate all "
    "combinations of well-formed parentheses.",
    [
        ("n = 3", "['((()))','(()())','(())()','()(())','()()()']"),
        ("n = 1", "['()']"),
    ],
    [
        "1 <= n <= 8",
    ],
    [
        "Backtrack: add '(' if we still have openers; add ')' if we have "
        "more opens than closes so far.",
        "Stop when the string has length 2n.",
    ],
    "def generate_parenthesis(n: int) -> list[str]:",
    """    out: list[str] = []

    def backtrack(s: str, opens: int, closes: int) -> None:
        if len(s) == 2 * n:
            out.append(s)
            return
        if opens < n:
            backtrack(s + '(', opens + 1, closes)
        if closes < opens:
            backtrack(s + ')', opens, closes + 1)

    backtrack('', 0, 0)
    return out""",
    [
        ((3,), ["((()))", "(()())", "(())()", "()(())", "()()()"]),
        ((1,), ["()"]),
    ],
    "public static List<String> generateParenthesis(int n)",
    """        List<String> out = new ArrayList<>();
        backtrack(out, new StringBuilder(), 0, 0, n);
        return out;
    }

    private static void backtrack(List<String> out, StringBuilder sb, int opens, int closes, int n) {
        if (sb.length() == 2 * n) {
            out.add(sb.toString());
            return;
        }
        if (opens < n) {
            sb.append('(');
            backtrack(out, sb, opens + 1, closes, n);
            sb.deleteCharAt(sb.length() - 1);
        }
        if (closes < opens) {
            sb.append(')');
            backtrack(out, sb, opens, closes + 1, n);
            sb.deleteCharAt(sb.length() - 1);
        }
    }""",
    [
        ("3", "[((())), (()()), (())(), ()(()), ()()()]"),  # won't pass; just for print
    ],
    """Backtracking. Two counts: how many `'('` we've placed and how many
`')'`. We can place another `'('` if `opens < n`. We can place another
`')'` if `closes < opens` (otherwise the prefix would be unbalanced).

**Time:** O(4^n / sqrt(n)) — the Catalan number. **Space:** O(n) recursion
depth.
""",
)

# 5. Daily Temperatures (Medium)
add(
    "05-daily-temperatures", "Daily Temperatures", "Medium",
    "Given an array of integers `temperatures` representing daily "
    "temperatures, return an array `answer` such that `answer[i]` is the "
    "number of days you have to wait after the ith day to get a warmer "
    "temperature. If there is no future day with a warmer temperature, set "
    "`answer[i] = 0`.",
    [
        ("temperatures = [73,74,75,71,69,72,76,73]", "[1,1,4,2,1,1,0,0]"),
        ("temperatures = [30,40,50,60]", "[1,1,1,0]"),
    ],
    [
        "1 <= len(temperatures) <= 10^5",
        "30 <= temperatures[i] <= 100",
    ],
    [
        "Monotonic stack: store indices of days with decreasing temperatures.",
        "When today's temp is higher than the top, the top is resolved.",
    ],
    "def daily_temperatures(temperatures: list[int]) -> list[int]:",
    """    n = len(temperatures)
    answer = [0] * n
    stack: list[int] = []   # indices, decreasing temperatures
    for i, t in enumerate(temperatures):
        while stack and temperatures[stack[-1]] < t:
            j = stack.pop()
            answer[j] = i - j
        stack.append(i)
    return answer""",
    [
        (([73, 74, 75, 71, 69, 72, 76, 73],), [1, 1, 4, 2, 1, 1, 0, 0]),
        (([30, 40, 50, 60],), [1, 1, 1, 0]),
        (([90, 80, 70, 60],), [0, 0, 0, 0]),
    ],
    "public static int[] dailyTemperatures(int[] temperatures)",
    """        int n = temperatures.length;
        int[] answer = new int[n];
        Deque<Integer> stack = new ArrayDeque<>();   // indices, decreasing temps
        for (int i = 0; i < n; i++) {
            while (!stack.isEmpty() && temperatures[stack.peek()] < temperatures[i]) {
                int j = stack.pop();
                answer[j] = i - j;
            }
            stack.push(i);
        }
        return answer""",
    [
        ("new int[]{73,74,75,71,69,72,76,73}", "[1, 1, 4, 2, 1, 1, 0, 0]"),
        ("new int[]{30,40,50,60}", "[1, 1, 1, 0]"),
    ],
    """Monotonic stack of indices with *strictly decreasing* temperatures.
For each new day, pop everything cooler and record the answer.

**Time:** O(n) — each index is pushed and popped at most once.
**Space:** O(n) in the worst case (monotonically decreasing input).
""",
)

# 6. Car Fleet (Medium)
add(
    "06-car-fleet", "Car Fleet", "Medium",
    "There are `n` cars going to the same destination along a one-lane "
    "road. The destination is `target` miles away. You are given two "
    "integer arrays `position` and `speed`, both of length `n`, where "
    "`position[i]` is the position of the ith car and `speed[i]` is its "
    "speed. A car can never pass another car ahead of it, but it can "
    "catch up to it and drive bumper-to-bumper at the same speed. A car "
    "fleet is a non-empty set of cars driving at the same speed with no "
    "cars ahead of them. Return the number of car fleets.",
    [
        ("target = 12, position = [10,8,0,5,3], speed = [2,4,1,1,3]", "3"),
        ("target = 10, position = [3], speed = [3]", "1"),
    ],
    [
        "n == position.length == speed.length",
        "1 <= n <= 10^5",
        "0 < target <= 10^6",
        "0 <= position[i] < target",
        "0 < speed[i] < 10^6",
    ],
    [
        "Sort cars by position descending (closest to target first).",
        "For each car, compute the time it would take alone. Stack of times; "
        "if the time is <= the fleet in front, it joins that fleet.",
    ],
    "def car_fleet(target: int, position: list[int], speed: list[int]) -> int:",
    """    cars = sorted(zip(position, speed), reverse=True)
    fleets = 0
    cur_time = 0.0
    for p, s in cars:
        time = (target - p) / s
        if time > cur_time:
            fleets += 1
            cur_time = time
    return fleets""",
    [
        ((12, [10, 8, 0, 5, 3], [2, 4, 1, 1, 3]), 3),
        ((10, [3], [3]), 1),
        ((100, [0, 2, 4], [4, 2, 1]), 1),  # the rear catches up to the front
    ],
    "public static int carFleet(int target, int[] position, int[] speed)",
    """        int n = position.length;
        Integer[] idx = new Integer[n];
        for (int i = 0; i < n; i++) idx[i] = i;
        Arrays.sort(idx, (a, b) -> Integer.compare(position[b], position[a]));
        int fleets = 0;
        double curTime = 0.0;
        for (int i : idx) {
            double time = (double)(target - position[i]) / speed[i];
            if (time > curTime) {
                fleets++;
                curTime = time;
            }
        }
        return fleets""",
    [
        ("12, new int[]{10,8,0,5,3}, new int[]{2,4,1,1,3}", "3"),
        ("10, new int[]{3}, new int[]{3}", "1"),
    ],
    """Sort cars by position descending. Compute each car's *time to target
alone*. A car joins the fleet in front if its time is `<=` the front car's
time. Otherwise, it starts a new fleet.

**Time:** O(n log n) for the sort. **Space:** O(n).
""",
)

# 7. Largest Rectangle In Histogram (Hard)
add(
    "07-largest-rectangle-in-histogram", "Largest Rectangle in Histogram",
    "Hard",
    "Given an array of integers `heights` representing the histogram's bar "
    "height where the width of each bar is 1, return the area of the largest "
    "rectangle that can be formed in the histogram.",
    [
        ("heights = [2,1,5,6,2,3]", "10"),
        ("heights = [2,4]", "4"),
    ],
    [
        "1 <= len(heights) <= 10^5",
        "0 <= heights[i] <= 10^4",
    ],
    [
        "Brute force: for each pair (l, r), compute min height and area. O(n²).",
        "Monotonic stack: for each bar, find the nearest smaller bar on "
        "each side. That's the width of the max rectangle where this bar "
        "is the limiting height.",
    ],
    "def largest_rectangle_area(heights: list[int]) -> int:",
    """    stack: list[int] = []   # indices, increasing heights
    best = 0
    for i, h in enumerate(heights + [0]):
        while stack and heights[stack[-1]] >= h:
            height = heights[stack.pop()]
            left = stack[-1] if stack else -1
            width = i - left - 1
            best = max(best, height * width)
        stack.append(i)
    return best""",
    [
        (([2, 1, 5, 6, 2, 3],), 10),
        (([2, 4],), 4),
        (([0],), 0),
        (([1, 1, 1, 1],), 4),
    ],
    "public static int largestRectangleArea(int[] heights)",
    """        Deque<Integer> stack = new ArrayDeque<>();
        int best = 0;
        int n = heights.length;
        for (int i = 0; i <= n; i++) {
            int h = (i == n) ? 0 : heights[i];
            while (!stack.isEmpty() && heights[stack.peek()] >= h) {
                int height = heights[stack.pop()];
                int left = stack.isEmpty() ? -1 : stack.peek();
                int width = i - left - 1;
                best = Math.max(best, height * width);
            }
            stack.push(i);
        }
        return best""",
    [
        ("new int[]{2,1,5,6,2,3}", "10"),
        ("new int[]{2,4}", "4"),
    ],
    """**Monotonic increasing stack** of indices. When we see a bar shorter
than the top, we pop and compute the area using the popped bar's height and
the current index (right boundary) and the new top's index (left boundary).

We append a sentinel `0` at the end so all remaining bars get popped and
accounted for.

**Time:** O(n). **Space:** O(n).
""",
)
