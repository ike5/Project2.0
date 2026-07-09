# Java 21 Cheatsheet for NeetCode 150 ☕

Handy Java 21 idioms you'll see in the solutions. We target **Java 21 (LTS)**
throughout — no `Vector`, no `Stack`, no `Hashtable`. Where modern features
help (records, `var`, `List.of`, pattern matching), we use them.

---

## Primitives & wrappers

| Primitive | Wrapper | Default | Notes |
|-----------|---------|---------|-------|
| `int`     | `Integer` | 0     | Beware of overflow (use `long` for products) |
| `long`    | `Long`    | 0L    | `long` is 64-bit |
| `double`  | `Double`  | 0.0   | `Double.isFinite(x)` |
| `char`    | `Character` | `'\u0000'` | A single UTF-16 code unit |
| `boolean` | `Boolean` | false | — |

`int[]` is a primitive array. `Integer[]` is an object array (autoboxed).

## Creating collections (immutable)

```java
List<Integer> list = List.of(1, 2, 3);            // immutable
List<Integer> mut  = new ArrayList<>(List.of(1,2,3));
Set<Integer>  set  = Set.of(1, 2, 3);
Map<String,Integer> map = Map.of("a", 1, "b", 2);
Map.Entry<String,Integer> e = Map.entry("a", 1);
```

`List.of`, `Set.of`, `Map.of` are **immutable**. To mutate, wrap in
`new ArrayList<>(List.of(...))`.

## Common mutable collections

```java
List<Integer> list = new ArrayList<>();
list.add(x); list.get(i); list.size();
list.sort(Comparator.naturalOrder());

Deque<Integer> dq = new ArrayDeque<>();   // stack AND queue, no nulls
dq.push(x);       // add to head     (stack push)
dq.pop();         // remove from head (stack pop)
dq.offer(x);      // add to tail
dq.poll();        // remove from head (queue)
dq.peek();        // peek at head     (queue)

Queue<Integer> q = new ArrayDeque<>();
q.offer(x); q.poll(); q.peek();

Stack<Integer> st = new Stack<>();        // legacy; prefer Deque
```

## Hash maps and sets

```java
Map<String, Integer> map = new HashMap<>();
map.put(k, v);
map.getOrDefault(k, 0);
map.merge(k, 1, Integer::sum);   // increment counter idiom
map.containsKey(k);
map.getOrDefault(k, 0) + 1;       // increment counter idiom 2

Set<Integer> set = new HashSet<>();
set.add(x); set.contains(x); set.remove(x);
```

## Priority queue (heap)

```java
// Min-heap
PriorityQueue<Integer> min = new PriorityQueue<>();
// Max-heap
PriorityQueue<Integer> max = new PriorityQueue<>(Comparator.reverseOrder());
// Custom
PriorityQueue<int[]> pq = new PriorityQueue<>((a, b) -> a[0] - b[0]);
pq.offer(x);   // add
pq.poll();     // remove min/max
pq.peek();     // peek
```

## Arrays helpers

```java
int[] a = {3, 1, 2};
Arrays.sort(a);                          // ascending
Arrays.sort(a, Collections.reverseOrder()); // boxed Integer[] only
Integer[] boxed = {3, 1, 2};
Arrays.sort(boxed);                      // needs Integer[]
List<Integer> l = Arrays.asList(boxed);  // fixed-size view
int idx = Arrays.binarySearch(a, 5);
String s = Arrays.toString(a);
List<List<Integer>> grid = new ArrayList<>();
int[][] g = new int[n][m];
```

## Strings

```java
String s = "abc";
char c = s.charAt(0);
int n = s.length();
String[] parts = s.split(",");
String joined = String.join(",", parts);
String sub = s.substring(0, 3);
boolean b = s.equals(other);            // never == for content
StringBuilder sb = new StringBuilder();
sb.append('x').append('y');
String out = sb.toString();
char[] ch = s.toCharArray();
```

## Maps with sorted keys (TreeMap)

```java
TreeMap<Integer, Integer> tm = new TreeMap<>();
tm.put(k, v);
tm.firstKey(); tm.lastKey();
tm.ceilingKey(x); tm.floorKey(x);
```

## LinkedList (rarely used in this course)

```java
LinkedList<Integer> ll = new LinkedList<>();
ll.addFirst(x); ll.addLast(x);
ll.peekFirst(); ll.peekLast();
ll.pollFirst(); ll.pollLast();
```

For most problems we use hand-rolled singly linked lists with a `Node` class.

## Records (Java 16+)

```java
public record Point(int x, int y) {}
Point p = new Point(1, 2);
int x = p.x();        // accessor method, not field
```

## `var` (Java 10+)

```java
var list = new ArrayList<Integer>();   // type inferred
var map  = new HashMap<String, Integer>();
```

## Pattern matching (Java 21)

```java
if (obj instanceof Integer i) {
    return i + 1;
}

switch (x) {
    case 1 -> "one";
    case 2, 3 -> "few";
    default -> "many";
}
```

## Text blocks (Java 15+)

Used for multi-line strings. The course doesn't lean on this; it's here for
reference.

## Math

```java
int  a = Math.abs(x);
int  m = Math.max(a, b);
int  g = Math.gcd(a, b);
long p = (long) a * b;          // cast BEFORE multiplying to avoid overflow
double r = Math.sqrt(x);
int  s = (int) Math.signum(x);
```

## Bit manipulation

```java
a & b, a | b, a ^ b, ~a
a << k, a >> k, a >>> k         // signed vs unsigned right shift
a & -a                          // lowest set bit
a & (a - 1)                     // clear the lowest set bit
Integer.bitCount(x)             // popcount
Integer.numberOfLeadingZeros(x)
Integer.numberOfTrailingZeros(x)
```

## Common patterns

**Adjacency list:**
```java
Map<Integer, List<Integer>> g = new HashMap<>();
g.computeIfAbsent(u, k -> new ArrayList<>()).add(v);
```

**BFS level-order:**
```java
Deque<int[]> q = new ArrayDeque<>();
q.offer(new int[]{start, 0});
while (!q.isEmpty()) {
    int[] cur = q.poll();
    int node = cur[0], dist = cur[1];
    for (int nei : g.getOrDefault(node, List.of())) {
        if (!seen.contains(nei)) {
            seen.add(nei);
            q.offer(new int[]{nei, dist + 1});
        }
    }
}
```

**DFS recursive:**
```java
void dfs(int u, int parent) {
    for (int v : g.getOrDefault(u, List.of())) {
        if (v != parent) dfs(v, u);
    }
}
```

**Two pointers opposite ends:**
```java
int l = 0, r = nums.length - 1;
while (l < r) {
    int s = nums[l] + nums[r];
    if (s == target) return new int[]{l, r};
    if (s < target) l++;
    else r--;
}
```

**Sliding window:**
```java
int l = 0;
for (int r = 0; r < s.length(); r++) {
    // add s.charAt(r) to window
    while (invalid()) {
        // remove s.charAt(l) from window
        l++;
    }
    // update answer
}
```

**Binary search on answer:**
```java
int lo = MIN, hi = MAX;
while (lo < hi) {
    int mid = lo + (hi - lo) / 2;   // avoid overflow
    if (feasible(mid)) hi = mid;
    else               lo = mid + 1;
}
return lo;
```

## Pitfalls to avoid

- **Overflow.** `(int) a * b` overflows if `a*b > Integer.MAX_VALUE`. Cast
  the first operand to `long`: `(long) a * b`.
- **`==` vs `.equals()`.** Use `==` for primitives, `.equals` for objects.
  `s1 == s2` is reference identity, not content.
- **Integer division.** `5 / 2 == 2`, not `2.5`. Use `Math.floorDiv` if you
  need negative-safe division.
- **ArrayList vs int[]**. `int[]` doesn't autobox, so `list.get(i)` returns
  `Integer` (or `int` with pattern matching), but you can write loops with
  `for (int x : arr)` directly.
- **Modifying a list while iterating** throws `ConcurrentModificationException`.
  Use an iterator or build a new list.
- **Recursive depth** can blow the stack. For deep recursion, convert to
  iterative with an explicit stack.
- **`String` concatenation in a loop** is O(n²). Use `StringBuilder`.
- **`Set.of` and `Map.of` reject `null`** keys/values. They throw NPE.
