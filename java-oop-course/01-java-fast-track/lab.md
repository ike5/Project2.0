# Lab 01 — Language Essentials Hands-On

**You'll:** spin up a small project and make the language fundamentals
concrete. ⏱️ ~40 min.

---

## Part A — A fresh project

```bash
mkdir -p ~/dev/ft01 && cd ~/dev/ft01
mkdir -p src/com/example/ft01
```

We'll keep all the parts below in a single class for fast iteration.

## Part B — Value vs. reference

`src/com/example/ft01/Types.java`:
```java
package com.example.ft01;

public class Types {
    public static void main(String[] args) {
        // 1. Primitives copy.
        int a = 5;
        int b = a;
        b = 99;
        System.out.println("primitives: a=" + a + " b=" + b);

        // 2. Reference sharing.
        int[] xs1 = {1, 2, 3};
        int[] xs2 = xs1;            // same array
        xs2[0] = 99;
        System.out.println("arrays: xs1[0]=" + xs1[0]);  // 99

        // 3. Strings are immutable references.
        String s1 = "hello";
        String s2 = s1;
        s2 = "world";                // reassigning the reference; s1 unchanged
        System.out.println("strings: s1=" + s1 + " s2=" + s2);
    }
}
```

Compile + run:
```bash
javac -d out $(find src -name '*.java')
java -cp out com.example.ft01.Types
```

Expected:
```
primitives: a=5 b=99
arrays: xs1[0]=99
strings: s1=hello s2=world
```

✅ Confirm the outputs. Re-read §1 of the README if the array line surprised
you — this is the most common Java footgun.

## Part C — `==` vs. `equals`

Add to the same class (or write a new one):
```java
String a = new String("hi");
String b = new String("hi");
System.out.println("==:      " + (a == b));         // false
System.out.println("equals:  " + a.equals(b));      // true

// String literals are interned:
String x = "hi";
String y = "hi";
System.out.println("literal ==: " + (x == y));      // true (compiler interns)
```

✅ Expected: `==: false`, `equals: true`, `literal ==: true`. The last one is
the *only* case where `==` works on `String`; never rely on it.

## Part D — Modern `switch` and pattern matching

```java
for (Object obj : new Object[]{42, "Ada", 3.14, true}) {
    String description = switch (obj) {
        case Integer i -> "int " + i;
        case String s  -> "string of length " + s.length();
        case Double d  -> "double " + d;
        case null      -> "null";
        default        -> "something else (" + obj.getClass().getSimpleName() + ")";
    };
    System.out.println(description);
}
```

✅ Expected:
```
int 42
string of length 3
double 3.14
something else (Boolean)
```

The compiler checks `switch` exhaustiveness when the type is sealed or an
enum. For `Object` you must provide a `default`.

## Part E — Strings, properly

```java
// formatted
String msg = "Name: %s, Age: %d".formatted("Ada", 36);
System.out.println(msg);

// text block
String json = """
        {
          "name": "Ada",
          "age":  36
        }""";
System.out.println(json);

// joins
String csv = String.join(", ", "a", "b", "c");
System.out.println(csv);

// null-safe checks
String input = "  ";
System.out.println("blank: " + input.isBlank());
System.out.println("null/empty: " + (input == null || input.isEmpty()));
```

## Part F — `null` discipline

```java
public static String shout(String s) {
    return Objects.requireNonNull(s, "s").toUpperCase();
}

try { System.out.println(shout(null)); }
catch (NullPointerException e) { System.out.println("rejected: " + e.getMessage()); }
System.out.println(shout("hi"));  // HI
```

✅ Expected: `rejected: s`, then `HI`. `Objects.requireNonNull` is the
idiomatic way to reject `null` at the API boundary.

## Part G — `var`

```java
var list = new ArrayList<String>();
list.add("a"); list.add("b");
var copy = List.copyOf(list);
System.out.println(copy.getClass().getSimpleName() + " " + copy);
```

`var` is a local-variable feature only. It doesn't change the type system
— the compiler still infers `ArrayList<String>`. Use it when the right-hand
side makes the type obvious.

## What you learned

- Primitives copy, reference types share — this drives a lot of behaviour.
- `==` is identity, `.equals` is value. For `String`, always use `equals`.
- `switch` is an expression, and `instanceof` pattern matching removes the
  two-step cast.
- `null` is *valid* for every reference type; make the API reject it
  explicitly with `Objects.requireNonNull`.
- `var` keeps Java's static types; use it for readability, not for "magic".

---

➡️ **[challenge.md](./challenge.md)** then [Module 02](../02-oop-foundations/).
