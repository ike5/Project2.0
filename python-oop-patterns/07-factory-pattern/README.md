# Module 07 — The factory pattern

**Python skill:** `classmethod`, building the right object by name, registries.
**LeetCode problem:** [707. Design Linked List](https://leetcode.com/problems/design-linked-list/) · Medium.
**Time:** ~1.5 h.

---

## 1. The pattern

A **factory** is a method (or function) that builds and returns the right object based on some input — a name, a config dict, a parsed file header, etc. The point is to keep the construction logic in *one place* so callers don't have to know which concrete class to pick.

```python
class Notifier:
    def send(self, to: str, msg: str) -> None: ...

class EmailNotifier(Notifier):
    def send(self, to: str, msg: str) -> None:
        print(f"[email to {to}] {msg}")

class SMSNotifier(Notifier):
    def send(self, to: str, msg: str) -> None:
        print(f"[SMS to {to}] {msg}")

class PushNotifier(Notifier):
    def send(self, to: str, msg: str) -> None:
        print(f"[push to {to}] {msg}")

class Notifier:
    _registry: dict[str, type[Notifier]] = {
        "email": EmailNotifier,
        "sms":   SMSNotifier,
        "push":  PushNotifier,
    }

    @classmethod
    def for_channel(cls, channel: str) -> "Notifier":
        return cls._registry[channel]()
```

`Notifier.for_channel("email")` returns an `EmailNotifier` instance. The caller doesn't need to know that `EmailNotifier` exists.

## 2. `@classmethod` — the key tool

Inside an ordinary method, `self` is the instance. Inside a `@classmethod`, `cls` is the *class itself*:

```python
class Date:
    def __init__(self, y, m, d): self.y, self.m, self.d = y, m, d

    @classmethod
    def from_string(cls, s: str) -> "Date":
        y, m, d = map(int, s.split("-"))
        return cls(y, m, d)         # cls(...) == Date(...) here
```

`cls(...)` builds a new instance of whatever class you called `from_string` on. That's what makes it work as a factory: if you subclass `Date` and call `MyDate.from_string(...)`, you get a `MyDate`.

For the registry version above, we just used the registry's class directly — no `cls` needed, because subclasses don't usually register themselves.

## 3. `@staticmethod` — almost the same, but no class

`@staticmethod` is a function in a class's namespace. It doesn't get `self` or `cls`. Useful for namespacing helpers, but rarely the right tool for a factory.

```python
class C:
    @staticmethod
    def add(a, b):
        return a + b

C.add(1, 2)   # 3
```

## 4. The LeetCode problem

> [707. Design Linked List](https://leetcode.com/problems/design-linked-list/)
>
> Design a singly linked list with these operations:
>
> - `get(index)` — return the value at `index`th node, or `-1` if out of range.
> - `addAtHead(val)` — prepend a node.
> - `addAtTail(val)` — append a node.
> - `addAtIndex(index, val)` — insert before the `index`th node (so `addAtIndex(0, val)` is a prepend; `addAtIndex(len, val)` is an append).
> - `deleteAtIndex(index)` — remove the `index`th node, no-op if out of range.

The **factory** angle here is mild: a `MyLinkedList.from_array(xs)` classmethod is a clean way to *build* a list from a Python list. Most of the lesson is the linked-list mechanics — which is a great exercise for keeping the cursor at the right node.

For the linked list, use a `ListNode` with `val` and `next` fields, and either a sentinel head node or a `size` counter:

```python
class ListNode:
    def __init__(self, val: int = 0, next: "ListNode | None" = None) -> None:
        self.val = val
        self.next = next


class MyLinkedList:
    def __init__(self) -> None:
        self.head = ListNode()     # sentinel
        self.size = 0

    def get(self, index: int) -> int:
        if index < 0 or index >= self.size:
            return -1
        cur = self.head.next
        for _ in range(index):
            cur = cur.next
        return cur.val

    def addAtHead(self, val: int) -> None:
        self.addAtIndex(0, val)

    def addAtTail(self, val: int) -> None:
        self.addAtIndex(self.size, val)

    def addAtIndex(self, index: int, val: int) -> None:
        if index < 0 or index > self.size:
            return
        cur = self.head
        for _ in range(index):
            cur = cur.next
        cur.next = ListNode(val, cur.next)
        self.size += 1

    def deleteAtIndex(self, index: int) -> None:
        if index < 0 or index >= self.size:
            return
        cur = self.head
        for _ in range(index):
            cur = cur.next
        cur.next = cur.next.next
        self.size -= 1
```

## 5. Anti-patterns

- **Giant `if/elif` chain on a string.** Use a dict registry instead.
- **`@staticmethod` for a factory that should be inherited.** Use `@classmethod`.
- **Returning a class instead of an instance.** Callers always want an instance; do the `()` in the factory.

---

**→ Next: [Module 08 — The adapter pattern](./../08-adapter-pattern/)**
