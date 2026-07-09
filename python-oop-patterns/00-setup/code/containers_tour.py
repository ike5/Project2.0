"""A tour of the Python containers we'll use throughout the course.

Run me: python 00-setup/code/containers_tour.py
"""

from collections import Counter, defaultdict, deque
import heapq


def show_list() -> None:
    xs = [3, 1, 4, 1, 5, 9, 2, 6]
    print("list")
    print("  xs          =", xs)
    print("  xs[0]       =", xs[0])            # O(1) index
    print("  xs[-1]      =", xs[-1])           # O(1) last
    print("  xs.append(7) ->", end=" ")
    xs.append(7)
    print(xs)
    print("  xs.pop()    =", xs.pop(), "->", xs)  # O(1) end
    print("  sorted(xs)  =", sorted(xs))          # O(n log n), new list


def show_dict() -> None:
    d = {"a": 1, "b": 2}
    print("dict")
    print("  d                =", d)
    print("  d['c'] = 3       ->", end=" ")
    d["c"] = 3
    print(d)
    print("  d.get('z', 0)    =", d.get("z", 0))   # default if missing
    print("  'a' in d         =", "a" in d)        # O(1) key check
    for k, v in d.items():
        print(f"  ({k!r}, {v!r})")


def show_set() -> None:
    s = {1, 2, 3, 2}
    print("set")
    print("  s                =", s)              # duplicates removed
    print("  3 in s           =", 3 in s)         # O(1) membership
    s.add(4)
    print("  after s.add(4)   =", s)


def show_tuple() -> None:
    t = (1, 2, 3)
    print("tuple (immutable, hashable)")
    print("  t                =", t)
    print("  hashable -> can be a dict key: d = {(1,2): 'pair'}")
    d = {(1, 2): "pair"}
    print("  d[(1,2)]         =", d[(1, 2)])


def show_counter() -> None:
    c = Counter("abracadabra")
    print("Counter")
    print("  Counter('abracadabra') =", dict(c))
    print("  most_common(2)         =", c.most_common(2))


def show_defaultdict() -> None:
    dd: defaultdict[str, list[int]] = defaultdict(list)
    dd["x"].append(1)
    dd["x"].append(2)
    dd["y"].append(3)
    print("defaultdict(list)")
    print("  dd                =", dict(dd))
    print("  no KeyError on missing keys — empty list is created")


def show_deque() -> None:
    q = deque([1, 2, 3])
    print("deque")
    print("  q                =", q)
    q.append(4)
    q.appendleft(0)
    print("  after append + appendleft =", q)
    print("  q.popleft()      =", q.popleft(), "->", q)


def show_heapq() -> None:
    h = [5, 1, 3, 8, 2]
    heapq.heapify(h)
    print("heapq (min-heap)")
    print("  h                =", h)
    print("  heappop          =", heapq.heappop(h), "->", h)
    heapq.heappush(h, 0)
    print("  after heappush(0) =", h)


def main() -> None:
    show_list()
    print()
    show_dict()
    print()
    show_set()
    print()
    show_tuple()
    print()
    show_counter()
    print()
    show_defaultdict()
    print()
    show_deque()
    print()
    show_heapq()


if __name__ == "__main__":
    main()
