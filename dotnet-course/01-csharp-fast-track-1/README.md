# Module 01 — C# Fast-Track I

**Goal:** get fluent in C#'s type system, control flow, and — the part that bites
newcomers — **nullability**. You already program, so this is brisk and contrast-driven.

⏱️ ~1.5 h · 🎯 Prereq: Module 00.

---

## 1. Two kinds of types (this matters constantly)

- **Value types** — `int`, `double`, `bool`, `char`, `decimal`, `struct`, `enum`.
  They hold their data *directly* and are **copied** on assignment / when passed.
- **Reference types** — `class`, `string`, arrays, `record` (by default), most things
  you `new`. The variable holds a *reference* to an object on the heap; assignment
  copies the reference, not the object.

```csharp
int a = 1; int b = a; b = 2;           // a is still 1 (copied)
var l1 = new List<int>(); var l2 = l1; // l1 and l2 are the SAME list
l2.Add(9);                             // l1.Count == 1
```
This explains "why did my change to one variable affect another?" — reference sharing.

`string` is a reference type but **immutable** — every "modification" makes a new string.

## 2. Nullability & nullable reference types (NRT)

Modern C# projects enable `<Nullable>enable</Nullable>`. Then:
- `string` means "shouldn't be null" — the compiler warns if you might assign null.
- `string?` means "may be null" — the compiler forces you to handle the null case.

```csharp
string name = GetName();        // compiler assumes non-null
string? maybe = TryGetName();   // could be null
int len = maybe?.Length ?? 0;   // null-conditional ?.  +  null-coalescing ??
maybe ??= "default";            // assign only if null
string forced = maybe!;         // null-forgiving: "trust me, not null" (use sparingly)
```
NRT turns a class of runtime `NullReferenceException`s into **compile-time warnings**.
Treat the warnings as errors mentally — they're the framework helping you.

Nullable *value* types use the same `?`: `int? count = null;` (a `Nullable<int>`).

## 3. Control flow (with modern twists)

```csharp
if/else, for, foreach, while, do/while   // as you'd expect

// switch EXPRESSION (returns a value):
string size = n switch { < 0 => "neg", 0 => "zero", < 10 => "small", _ => "big" };

// pattern matching with 'is':
if (obj is string s && s.Length > 3) { /* s is in scope, non-null */ }
```

## 4. Methods

```csharp
int Add(int a, int b) => a + b;                 // expression-bodied
void Log(string msg, int level = 1) { }          // default parameter
int Sum(params int[] xs) => xs.Sum();            // variadic
bool TryParse(string s, out int value) { value = 0; return false; } // out
void Bump(ref int x) => x++;                      // ref (modify caller's variable)
```
Arguments to **value-type** params are copied; to **reference-type** params, the
*reference* is copied (so you can mutate the object, but reassigning the param
doesn't affect the caller unless `ref`).

## 5. Strings you'll actually use

```csharp
var s = $"{name} is {age}";                  // interpolation
var path = Path.Combine("a", "b");           // don't hand-concat paths
var upper = s.ToUpperInvariant();
var parts = csv.Split(',');
var joined = string.Join(", ", parts);
bool empty = string.IsNullOrWhiteSpace(s);
var raw = """C:\no\escapes\needed""";        // raw string literal
```

---

## Do the lab
Create a console project, exercise value-vs-reference and nullability until the
behavior is obvious, and read the playground's `TypesDemo`. 👉 **[lab.md](./lab.md)**

Then: 👉 **[challenge.md](./challenge.md)**

## Key terms
value type · reference type · nullable reference types · `?.` · `??` · `!` ·
switch expression · pattern matching · `out`/`ref` · expression-bodied member

**Next →** [Module 02: C# Fast-Track II (OOP)](../02-csharp-fast-track-2-oop/)
