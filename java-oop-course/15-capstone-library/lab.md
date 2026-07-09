# Lab 15 — Library Management System

**You'll:** build a working, modular, tested Library Management System
in five stages. ⏱️ ~5+ h.

---

## Stage 0 — Set up

```bash
mkdir -p ~/dev/oop15 && cd ~/dev/oop15
mkdir -p src/main/java/com/example/library/{model,service,io,util}
mkdir -p src/main/resources
mkdir -p data
```

## Stage 1 — The domain (model package)

`src/main/java/com/example/library/model/Book.java`:
```java
package com.example.library.model;

import java.util.Objects;

public record Book(String isbn, String title, String author) {
    public Book {
        Objects.requireNonNull(isbn, "isbn");
        Objects.requireNonNull(title, "title");
        Objects.requireNonNull(author, "author");
        if (isbn.isBlank()) throw new IllegalArgumentException("isbn must not be blank");
    }
}
```

`Member.java` and `Loan.java` follow the same pattern. Add a
`record Loan(long id, Book book, Member member, LocalDate borrowedOn,
LocalDate dueOn)`.

## Stage 2 — `Result<T, E>` (util package)

`src/main/java/com/example/library/util/Result.java`:
```java
package com.example.library.util;

public sealed interface Result<T, E> permits Result.Ok, Result.Err {
    record Ok<T, E>(T value)  implements Result<T, E> {}
    record Err<T, E>(E error) implements Result<T, E> {}

    static <T, E> Result<T, E> ok(T value)  { return new Ok<>(value); }
    static <T, E> Result<T, E> err(E error) { return new Err<>(error); }

    default boolean isOk() { return this instanceof Ok; }
    default T orElseThrow() {
        return switch (this) {
            case Ok<T, E> ok  -> ok.value();
            case Err<T, E> err -> { throw new IllegalStateException("Result is Err: " + err.error()); }
        };
    }
}
```

## Stage 3 — `Repository<T, ID>` and `InMemoryRepository<T, ID>`

`src/main/java/com/example/library/service/Repository.java`:
```java
package com.example.library.service;

import com.example.library.util.Result;
import java.util.List;
import java.util.Optional;

public interface Repository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll();
    Result<T, String> save(T value);
    boolean deleteById(ID id);
    int size();
}
```

`InMemoryRepository<T, ID>`:
```java
package com.example.library.service;

import com.example.library.util.Result;
import java.util.*;
import java.util.concurrent.ConcurrentHashMap;

public final class InMemoryRepository<T, ID> implements Repository<T, ID> {
    private final Map<ID, T> store = new ConcurrentHashMap<>();
    private final Function<T, ID> idExtractor;

    public InMemoryRepository(Function<T, ID> idExtractor) {
        this.idExtractor = idExtractor;
    }

    @Override public Optional<T> findById(ID id)         { return Optional.ofNullable(store.get(id)); }
    @Override public List<T> findAll()                  { return List.copyOf(store.values()); }
    @Override public Result<T, String> save(T value)    { store.put(idExtractor.apply(value), value); return Result.ok(value); }
    @Override public boolean deleteById(ID id)          { return store.remove(id) != null; }
    @Override public int size()                         { return store.size(); }
}
```

## Stage 4 — The `Library` service

`src/main/java/com/example/library/service/Library.java`:
```java
package com.example.library.service;

import com.example.library.model.*;
import com.example.library.util.Result;

import java.time.Clock;
import java.time.LocalDate;
import java.util.*;
import java.util.concurrent.atomic.AtomicLong;

public final class Library {
    private final Repository<Book, String>   books;
    private final Repository<Member, Long>  members;
    private final Repository<Loan, Long>    loans;
    private final Clock clock;
    private final int maxLoansPerMember;
    private final int loanDays;
    private final long centsPerDayFine;
    private final AtomicLong nextLoanId = new AtomicLong(1);

    public Library(Repository<Book, String> books,
                   Repository<Member, Long> members,
                   Repository<Loan, Long> loans,
                   Clock clock,
                   int maxLoansPerMember,
                   int loanDays,
                   long centsPerDayFine) {
        this.books = books;
        this.members = members;
        this.loans = loans;
        this.clock = clock;
        this.maxLoansPerMember = maxLoansPerMember;
        this.loanDays = loanDays;
        this.centsPerDayFine = centsPerDayFine;
    }

    public Result<Member, String> addMember(String name, String email) {
        if (name == null || name.isBlank()) return Result.err("name required");
        if (email == null || !email.contains("@")) return Result.err("valid email required");
        long id = Math.abs(Objects.hash(name, email, System.nanoTime()));
        Member m = new Member(id, name, email);
        return members.save(m);
    }

    public Result<Book, String> addBook(String isbn, String title, String author) {
        try {
            Book b = new Book(isbn, title, author);
            return books.save(b);
        } catch (Exception e) {
            return Result.err(e.getMessage());
        }
    }

    public Result<Loan, String> checkout(String isbn, long memberId) {
        var book = books.findById(isbn);
        if (book.isEmpty()) return Result.err("no such book: " + isbn);
        var member = members.findById(memberId);
        if (member.isEmpty()) return Result.err("no such member: " + memberId);

        // No double loans.
        boolean alreadyLoaned = loans.findAll().stream()
                .anyMatch(l -> l.book().isbn().equals(isbn));
        if (alreadyLoaned) return Result.err("book already on loan: " + isbn);

        // Limit per member.
        long active = loans.findAll().stream()
                .filter(l -> l.member().id() == memberId)
                .count();
        if (active >= maxLoansPerMember) return Result.err("member has too many loans");

        LocalDate today = LocalDate.now(clock);
        Loan loan = new Loan(nextLoanId.getAndIncrement(), book.get(), member.get(), today, today.plusDays(loanDays));
        return loans.save(loan);
    }

    public Result<Loan, String> returnBook(long loanId) {
        var loan = loans.findById(loanId);
        if (loan.isEmpty()) return Result.err("no such loan: " + loanId);
        loans.deleteById(loanId);
        return Result.ok(loan.get());
    }

    public long fineFor(Loan loan) {
        LocalDate today = LocalDate.now(clock);
        if (!today.isAfter(loan.dueOn())) return 0;
        long overdueDays = java.time.temporal.ChronoUnit.DAYS.between(loan.dueOn(), today);
        return overdueDays * centsPerDayFine;
    }

    public List<Loan> overdueLoans() {
        LocalDate today = LocalDate.now(clock);
        return loans.findAll().stream()
                .filter(l -> today.isAfter(l.dueOn()))
                .toList();
    }

    public List<Book>  books()   { return books.findAll(); }
    public List<Member> members(){ return members.findAll(); }
    public List<Loan>   loans()  { return loans.findAll(); }
}
```

## Stage 5 — The CLI `Main`

`src/main/java/com/example/library/Main.java`:
```java
package com.example.library;

import com.example.library.model.*;
import com.example.library.service.*;
import com.example.library.util.Result;

import java.time.Clock;
import java.util.Scanner;

public class Main {
    public static void main(String[] args) {
        Library lib = new Library(
                new InMemoryRepository<>(Book::isbn),
                new InMemoryRepository<>(Member::id),
                new InMemoryRepository<>(Loan::id),
                Clock.systemUTC(),
                3, 14, 25);

        try (var in = new Scanner(System.in)) {
            System.out.println("Library CLI — type 'help' for commands");
            while (in.hasNextLine()) {
                String line = in.nextLine().trim();
                if (line.isEmpty()) continue;
                if (line.equals("quit") || line.equals("exit")) break;
                dispatch(lib, line);
            }
        }
    }

    static void dispatch(Library lib, String line) {
        var parts = line.split("\\s+", 2);
        var cmd = parts[0];
        var rest = parts.length > 1 ? parts[1] : "";
        try {
            switch (cmd) {
                case "help" -> System.out.println("""
                        add member <name> <email>
                        add book  <isbn> <title> <author>
                        checkout <isbn> <memberId>
                        return <loanId>
                        list books | members | loans | overdue
                        fines
                        quit
                        """);
                case "add" -> handleAdd(lib, rest);
                case "checkout" -> handleCheckout(lib, rest);
                case "return" -> handleReturn(lib, rest);
                case "list" -> handleList(lib, rest);
                case "fines" -> handleFines(lib);
                default -> System.out.println("unknown: " + cmd);
            }
        } catch (Exception e) {
            System.out.println("ERROR: " + e.getMessage());
        }
    }

    static void handleAdd(Library lib, String rest) {
        var parts = rest.split("\\s+", 2);
        switch (parts[0]) {
            case "member" -> {
                var fields = parts[1].split("\\s+", 2);
                var r = lib.addMember(fields[0], fields[1]);
                System.out.println(r.isOk() ? "OK: " + r.orElseThrow() : "ERROR: " + ((Result.Err<?, ?>) r).error());
            }
            case "book" -> {
                var fields = parts[1].split("\\s+", 3);
                var r = lib.addBook(fields[0], fields[1], fields[2]);
                System.out.println(r.isOk() ? "OK: " + r.orElseThrow() : "ERROR: " + ((Result.Err<?, ?>) r).error());
            }
            default -> System.out.println("add what?");
        }
    }

    static void handleCheckout(Library lib, String rest) {
        var fields = rest.split("\\s+");
        var r = lib.checkout(fields[0], Long.parseLong(fields[1]));
        System.out.println(r.isOk() ? "OK: loan " + r.orElseThrow().id() : "ERROR: " + ((Result.Err<?, ?>) r).error());
    }

    static void handleReturn(Library lib, String rest) {
        var r = lib.returnBook(Long.parseLong(rest));
        System.out.println(r.isOk() ? "OK: returned loan " + r.orElseThrow().id() : "ERROR: " + ((Result.Err<?, ?>) r).error());
    }

    static void handleList(Library lib, String rest) {
        switch (rest) {
            case "books"    -> lib.books().forEach(System.out::println);
            case "members"  -> lib.members().forEach(System.out::println);
            case "loans"    -> lib.loans().forEach(System.out::println);
            case "overdue"  -> lib.overdueLoans().forEach(System.out::println);
            default -> System.out.println("list what?");
        }
    }

    static void handleFines(Library lib) {
        lib.loans().forEach(l -> System.out.println(l + " -> fine " + lib.fineFor(l) + " cents"));
    }
}
```

Compile + run:
```bash
cd src/main/java
javac -d ../../out $(find . -name '*.java')
cd ../..
java -cp out com.example.library.Main
```

Try:
```
add book 1234 "Programming in Java" "Deitel"
add member 1 Ada ada@example.com
checkout 1234 1
list loans
fines
quit
```

## Stage 6 — Make it modular

Add a `module-info.java` to `src/main/java/`:
```java
module com.example.library {
    exports com.example.library.model;
    exports com.example.library.util;
    exports com.example.library.service;
    // io not exported to enforce layering
}
```

Compile + package as a modular JAR; run with `--module-path`.

## Stage 7 — Tests (optional but recommended)

A small JUnit 5 test for `Library.checkout`:
```java
@Test
void cannotCheckoutBookAlreadyOnLoan() {
    var books   = new InMemoryRepository<Book, String>(Book::isbn);
    var members = new InMemoryRepository<Member, Long>(Member::id);
    var loans   = new InMemoryRepository<Loan, Long>(Loan::id);
    books.save(new Book("1234", "t", "a"));
    members.save(new Member(1, "ada", "ada@x"));
    members.save(new Member(2, "bob", "bob@x"));

    var lib = new Library(books, members, loans, Clock.systemUTC(), 3, 14, 25);
    assertTrue(lib.checkout("1234", 1).isOk());
    var r2 = lib.checkout("1234", 2);
    assertFalse(r2.isOk());
}
```

---

## What you learned

- A real application layered cleanly with package boundaries.
- Generic `Repository<T, ID>` enabling interchangeable backends.
- Sealed `Result<T, E>` for business failures instead of exceptions.
- `Clock` injection for testability.
- `module-info.java` enforcing layering via `exports`.

➡️ **[challenge.md](./challenge.md)** then back to [Module 00](../README.md).
