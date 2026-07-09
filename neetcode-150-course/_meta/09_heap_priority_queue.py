"""Module 09 — Heap / Priority Queue problem catalog."""

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


# 1. Kth Largest Element in a Stream (Easy)
add(
    "01-kth-largest-element-in-a-stream", "Kth Largest Element in a Stream",
    "Easy",
    "Design a class to find the kth largest element in a stream. Note "
    "that it is the kth largest element in the sorted order, not the kth "
    "distinct element. Implement `KthLargest` with `add(val)`.",
    [
        ("KthLargest(3, [4, 5, 8, 2]); add(3) -> 4; add(5) -> 5; "
         "add(10) -> 5; add(9) -> 8; add(4) -> 8",
         "4, 5, 5, 8, 8"),
    ],
    [
        "1 <= k <= 10^4",
        "0 <= len(nums) <= 10^4",
        "-10^4 <= val <= 10^4",
        "At most 10^4 calls to add",
    ],
    [
        "Min-heap of size k. The top is the kth largest.",
    ],
    "class KthLargest:",
    """    def __init__(self, k: int, nums: list[int]) -> None:
        import heapq
        self.k = k
        self.heap: list[int] = []
        for n in nums:
            self.add(n)

    def add(self, val: int) -> int:
        import heapq
        heapq.heappush(self.heap, val)
        if len(self.heap) > self.k:
            heapq.heappop(self.heap)
        return self.heap[0]""",
    [
        (("__init__", 3, [4, 5, 8, 2]), None),
    ],
    "public static int add(int val) { return -1; /* placeholder */ }",
    """    public static class KthLargest {
        private final int k;
        private final PriorityQueue<Integer> heap = new PriorityQueue<>();
        public KthLargest(int k, int[] nums) {
            this.k = k;
            for (int n : nums) add(n);
        }
        public int add(int val) {
            heap.offer(val);
            if (heap.size() > k) heap.poll();
            return heap.peek();
        }
    }""",
    [],
    """A **min-heap of size k** holds the k largest values seen so far.
The smallest of those is the kth largest overall. Insert and trim to
size k after each `add`.

**Time:** O(log k) per add. **Space:** O(k).
""",
)

# 2. Last Stone Weight (Easy)
add(
    "02-last-stone-weight", "Last Stone Weight", "Easy",
    "You are given an array of integers `stones` where `stones[i]` is the "
    "weight of the ith stone. Each turn, we choose the two heaviest stones "
    "and smash them together. If the stones are equal, both are destroyed. "
    "Otherwise, the lighter stone is destroyed and the heavier stone has its "
    "weight reduced by the lighter's. Return the smallest possible weight "
    "of the last stone (or 0 if no stones remain).",
    [
        ("stones = [2,7,4,1,8,1]", "1"),
        ("stones = [1]", "1"),
    ],
    [
        "1 <= len(stones) <= 30",
        "1 <= stones[i] <= 1000",
    ],
    [
        "A max-heap. Pop two, push the difference (or nothing if equal).",
    ],
    "def last_stone_weight(stones: list[int]) -> int:",
    """    import heapq
    heap = [-s for s in stones]
    heapq.heapify(heap)
    while len(heap) > 1:
        a = -heapq.heappop(heap)
        b = -heapq.heappop(heap)
        if a != b:
            heapq.heappush(heap, -(a - b))
    return -heap[0] if heap else 0""",
    [
        (([2, 7, 4, 1, 8, 1],), 1),
        (([1],), 1),
        (([2, 2],), 0),
    ],
    "public static int lastStoneWeight(int[] stones)",
    """        PriorityQueue<Integer> heap = new PriorityQueue<>(Comparator.reverseOrder());
        for (int s : stones) heap.offer(s);
        while (heap.size() > 1) {
            int a = heap.poll(), b = heap.poll();
            if (a != b) heap.offer(a - b);
        }
        return heap.isEmpty() ? 0 : heap.poll()""",
    [
        ("new int[]{2,7,4,1,8,1}", "1"),
        ("new int[]{1}", "1"),
    ],
    """A max-heap. Pop two heaviest, push the difference if any. Repeat
until at most one remains.

**Time:** O(n log n). **Space:** O(n).
""",
)

# 3. K Closest Points to Origin (Medium)
add(
    "03-k-closest-points-to-origin", "K Closest Points to Origin", "Medium",
    "Given an array of `points` where `points[i] = [xi, yi]` represents a "
    "point on the X-Y plane and an integer `k`, return the `k` closest "
    "points to the origin (0, 0). The distance is the Euclidean distance "
    "(`sqrt(x^2 + y^2)`). You may return the answer in any order.",
    [
        ("points = [[1,3],[-2,2]], k = 2", "[[-2,2],[1,3]]"),
        ("points = [[3,3],[5,-1],[-2,4]], k = 2", "[[3,3],[-2,4]]"),
    ],
    [
        "1 <= k <= len(points) <= 10^4",
        "-10^4 <= xi, yi <= 10^4",
    ],
    [
        "Use a max-heap of size k keyed on squared distance.",
        "Or quickselect (O(n) average, O(n^2) worst).",
    ],
    "def k_closest(points: list[list[int]], k: int) -> list[list[int]]:",
    """    import heapq
    heap: list[tuple[int, list[int]]] = []
    for p in points:
        d = p[0] * p[0] + p[1] * p[1]
        heapq.heappush(heap, (-d, p))
        if len(heap) > k:
            heapq.heappop(heap)
    return [p for _, p in heap]""",
    [
        (([[1, 3], [-2, 2]], 2), [[-2, 2], [1, 3]]),
        (([[3, 3], [5, -1], [-2, 4]], 2), [[3, 3], [-2, 4]]),
    ],
    "public static int[][] kClosest(int[][] points, int k)",
    """        PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> {
            int da = a[0] * a[0] + a[1] * a[1];
            int db = b[0] * b[0] + b[1] * b[1];
            return Integer.compare(db, da);  // max-heap on distance
        });
        for (int[] p : points) {
            heap.offer(p);
            if (heap.size() > k) heap.poll();
        }
        int[][] out = new int[heap.size()][];
        return heap.toArray(out)""",
    [
        ("new int[][]{{1,3},{-2,2}}, 2", "[[-2, 2], [1, 3]]"),
    ],
    """Max-heap of size k keyed on squared distance. The `sqrt` cancels
out (it's monotone), so we can compare squared distances.

**Time:** O(n log k). **Space:** O(k).
""",
)

# 4. Kth Largest Element in an Array (Medium)
add(
    "04-kth-largest-element-in-an-array", "Kth Largest Element in an Array",
    "Medium",
    "Given an integer array `nums` and an integer `k`, return the kth "
    "largest element in the array. Note that it is the kth largest in the "
    "sorted order, not the kth distinct element. You must solve it in "
    "O(n) time on average.",
    [
        ("nums = [3,2,1,5,6,4], k = 2", "5"),
        ("nums = [3,2,3,1,2,4,5,5,6], k = 4", "4"),
    ],
    [
        "1 <= k <= len(nums) <= 10^5",
        "-10^4 <= nums[i] <= 10^4",
    ],
    [
        "Min-heap of size k: O(n log k) — easy.",
        "Quickselect: O(n) average, O(n^2) worst.",
    ],
    "def kth_largest(nums: list[int], k: int) -> int:",
    """    import heapq
    return heapq.nlargest(k, nums)[-1]""",
    [
        (([3, 2, 1, 5, 6, 4], 2), 5),
        (([3, 2, 3, 1, 2, 4, 5, 5, 6], 4), 4),
    ],
    "public static int kthLargest(int[] nums, int k)",
    """        PriorityQueue<Integer> heap = new PriorityQueue<>();
        for (int n : nums) {
            heap.offer(n);
            if (heap.size() > k) heap.poll();
        }
        return heap.peek()""",
    [
        ("new int[]{3,2,1,5,6,4}, 2", "5"),
        ("new int[]{3,2,3,1,2,4,5,5,6}, 4", "4"),
    ],
    """The simplest is `heapq.nlargest(k, nums)[-1]` in Python or a
min-heap of size k. Quickselect is O(n) average but O(n^2) worst and
trickier to write.

**Time:** O(n log k) with heap; O(n) average with quickselect.
""",
)

# 5. Task Scheduler (Medium)
add(
    "05-task-scheduler", "Task Scheduler", "Medium",
    "You are given an array of CPU tasks, each labeled with a letter from "
    "A to Z, and a number `n`. Each interval, the CPU can execute a task "
    "or be idle. There must be at least `n` intervals between executions "
    "of the same task. Return the minimum number of intervals the CPU "
    "needs to finish all tasks.",
    [
        ("tasks = ['A','A','A','B','B','B'], n = 2", "8"),
        ("tasks = ['A','A','A','B','B','B'], n = 0", "6"),
    ],
    [
        "1 <= task.length <= 10^4",
        "tasks[i] is an uppercase English letter",
        "0 <= n <= 100",
    ],
    [
        "Count frequencies. The most-frequent task sets the lower bound.",
        "Answer = max(len(tasks), (max_freq - 1) * (n + 1) + count_max).",
    ],
    "def least_interval(tasks: list[str], n: int) -> int:",
    """    from collections import Counter
    counts = Counter(tasks)
    max_freq = max(counts.values())
    n_max = sum(1 for c in counts.values() if c == max_freq)
    return max(len(tasks), (max_freq - 1) * (n + 1) + n_max)""",
    [
        ((["A", "A", "A", "B", "B", "B"], 2), 8),
        ((["A", "A", "A", "B", "B", "B"], 0), 6),
        ((["A", "A", "A", "A", "A", "A", "B", "C", "D", "E", "F", "G"], 2), 16),
    ],
    "public static int leastInterval(char[] tasks, int n)",
    """        int[] count = new int[26];
        for (char t : tasks) count[t - 'A']++;
        int maxFreq = 0;
        for (int c : count) maxFreq = Math.max(maxFreq, c);
        int nMax = 0;
        for (int c : count) if (c == maxFreq) nMax++;
        int partCount = (maxFreq - 1) * (n + 1) + nMax;
        return Math.max(tasks.length, partCount)""",
    [
        ("new char[]{'A','A','A','B','B','B'}, 2", "8"),
        ("new char[]{'A','A','A','B','B','B'}, 0", "6"),
    ],
    """The most-frequent task determines a skeleton: `max_freq - 1` gaps
of length `n + 1` (the task plus its cooldown slots). The remaining
tasks fit into those gaps. If there are more tasks than slots, the
answer is just `len(tasks)`.

**Time:** O(n). **Space:** O(26).
""",
)

# 6. Design Twitter (Medium)
add(
    "06-design-twitter", "Design Twitter", "Medium",
    "Design a simplified version of Twitter where users can post tweets, "
    "follow / unfollow another user, and see the 10 most recent tweet IDs "
    "in the user's news feed. Implement the `Twitter` class.",
    [
        ("postTweet(1, 5); getNewsFeed(1) -> [5]; follow(1, 2); "
         "postTweet(2, 6); getNewsFeed(1) -> [6, 5]; unfollow(1, 2); "
         "getNewsFeed(1) -> [5]",
         "[5], [6, 5], [5]"),
    ],
    [
        "1 <= userId, followerId, followeeId <= 500",
        "0 <= tweetId <= 10^4",
        "At most 3 * 10^4 calls total",
    ],
    [
        "Each user has a list of their own tweets (with timestamps).",
        "News feed: merge the most recent tweets of the user and followees "
        "using a heap of size 10.",
    ],
    "class Twitter:",
    """    def __init__(self) -> None:
        self._tweets: dict[int, list[tuple[int, int]]] = {}
        self._follows: dict[int, set[int]] = {}
        self._time = 0

    def post_tweet(self, user_id: int, tweet_id: int) -> None:
        self._tweets.setdefault(user_id, []).append((self._time, tweet_id))
        self._time += 1

    def get_news_feed(self, user_id: int) -> list[int]:
        import heapq
        heap: list[tuple[int, int, int]] = []   # (-time, idx, tweet_id)
        users = self._follows.get(user_id, set()) | {user_id}
        for u in users:
            if not self._tweets.get(u):
                continue
            i = len(self._tweets[u]) - 1
            t, tid = self._tweets[u][i]
            heapq.heappush(heap, (-t, i, tid))
        out: list[int] = []
        while heap and len(out) < 10:
            neg_t, i, tid = heapq.heappop(heap)
            out.append(tid)
            if i > 0:
                t, tid2 = self._tweets[users_lookup(heap, users)][i - 1]
                heapq.heappush(heap, (-t, i - 1, tid2))
        return out

    def follow(self, follower_id: int, followee_id: int) -> None:
        self._follows.setdefault(follower_id, set()).add(followee_id)

    def unfollow(self, follower_id: int, followee_id: int) -> None:
        self._follows.get(follower_id, set()).discard(followee_id)""",
    [
        (("__init__",), None),
    ],
    "public static class Twitter",
    """        private int time = 0;
        private final Map<Integer, List<int[]>> tweets = new HashMap<>();
        private final Map<Integer, Set<Integer>> follows = new HashMap<>();
        public void postTweet(int userId, int tweetId) {
            tweets.computeIfAbsent(userId, k -> new ArrayList<>()).add(new int[]{time++, tweetId});
        }
        public List<Integer> getNewsFeed(int userId) {
            Set<Integer> users = new HashSet<>(follows.getOrDefault(userId, Set.of()));
            users.add(userId);
            PriorityQueue<int[]> heap = new PriorityQueue<>((a, b) -> Integer.compare(b[0], a[0]));
            // heap entry: [time, userId, index]
            for (int u : users) {
                List<int[]> ts = tweets.get(u);
                if (ts != null && !ts.isEmpty()) {
                    int i = ts.size() - 1;
                    heap.offer(new int[]{ts.get(i)[0], u, i});
                }
            }
            List<Integer> out = new ArrayList<>();
            while (!heap.isEmpty() && out.size() < 10) {
                int[] top = heap.poll();
                out.add(tweets.get(top[1]).get(top[2])[1]);
                if (top[2] > 0) {
                    int i = top[2] - 1;
                    heap.offer(new int[]{tweets.get(top[1]).get(i)[0], top[1], i});
                }
            }
            return out;
        }
        public void follow(int followerId, int followeeId) {
            follows.computeIfAbsent(followerId, k -> new HashSet<>()).add(followeeId);
        }
        public void unfollow(int followerId, int followeeId) {
            Set<Integer> s = follows.get(followerId);
            if (s != null) s.remove(followeeId);
        }""",
    [],
    """Each user has a list of `(time, tweet_id)` pairs (newest last).
The news feed is the 10 most recent tweets from the user and their
followees. Use a **max-heap on timestamp** with lazy next-tweet fetch
(merge k sorted lists).

**Time:** getNewsFeed O(F log F) where F is the number of followees.
**Space:** O(U + T).
""",
)

# 7. Find Median from Data Stream (Hard)
add(
    "07-find-median-from-data-stream", "Find Median from Data Stream",
    "Hard",
    "The **median** is the middle value in an ordered integer list. If the "
    "size of the list is even, there is no middle value, and the median "
    "is the mean of the two middle values. Implement the `MedianFinder` "
    "class: `add_num(int)` and `find_median() -> float`.",
    [
        ("MedianFinder(); addNum(1); addNum(2); findMedian() -> 1.5; "
         "addNum(3); findMedian() -> 2.0",
         "1.5, 2.0"),
    ],
    [
        "-10^5 <= num <= 10^5",
        "At most 5 * 10^4 calls to addNum and findMedian",
        "At least one call to findMedian after addNum",
    ],
    [
        "Two heaps: a max-heap of the small half and a min-heap of the "
        "large half. The median is at the top of one or the average of "
        "both.",
    ],
    "class MedianFinder:",
    """    def __init__(self) -> None:
        import heapq
        self.small: list[int] = []   # max-heap (negated)
        self.large: list[int] = []   # min-heap

    def add_num(self, num: int) -> None:
        import heapq
        heapq.heappush(self.small, -num)
        # make sure every element in small is <= every element in large
        if self.large and -self.small[0] > self.large[0]:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        # rebalance sizes
        if len(self.small) > len(self.large) + 1:
            heapq.heappush(self.large, -heapq.heappop(self.small))
        elif len(self.large) > len(self.small):
            heapq.heappush(self.small, -heapq.heappop(self.large))

    def find_median(self) -> float:
        if len(self.small) > len(self.large):
            return -self.small[0]
        return (-self.small[0] + self.large[0]) / 2.0""",
    [
        (("__init__",), None),
    ],
    "public static class MedianFinder",
    """        private final PriorityQueue<Integer> small = new PriorityQueue<>(Comparator.reverseOrder());
        private final PriorityQueue<Integer> large = new PriorityQueue<>();
        public void addNum(int num) {
            small.offer(num);
            if (!large.isEmpty() && small.peek() > large.peek()) {
                large.offer(small.poll());
            }
            if (small.size() > large.size() + 1) {
                large.offer(small.poll());
            } else if (large.size() > small.size()) {
                small.offer(large.poll());
            }
        }
        public double findMedian() {
            if (small.size() > large.size()) return small.peek();
            return (small.peek() + large.peek()) / 2.0;
        }""",
    [],
    """Two heaps:
- **max-heap `small`** holds the lower half.
- **min-heap `large`** holds the upper half.

After each `addNum`, rebalance so that `|len(small) - len(large)| <= 1`.

The median is `small.top` (if `small` is bigger) or the average of
`small.top` and `large.top`.

**Time:** O(log n) per addNum, O(1) per findMedian.
""",
)
