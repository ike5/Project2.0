package com.example.library;

import com.example.library.model.Book;
import com.example.library.model.Loan;
import com.example.library.model.Member;
import com.example.library.service.InMemoryRepository;
import com.example.library.service.Library;

import java.time.Clock;
import java.time.LocalDate;
import java.time.ZoneOffset;

/**
 * A tiny, dependency-free test driver. The full project should use JUnit 5;
 * this file is here so the solution has *some* automated coverage that runs
 * with just the JDK.
 */
public final class LibraryTest {

    public static void main(String[] args) {
        int failed = 0;
        failed += run("cannotCheckoutBookAlreadyOnLoan", LibraryTest::cannotCheckoutBookAlreadyOnLoan);
        failed += run("maxLoansPerMemberEnforced",      LibraryTest::maxLoansPerMemberEnforced);
        failed += run("fineForOverdue",                 LibraryTest::fineForOverdue);
        failed += run("addBookRejectsBlankIsbn",        LibraryTest::addBookRejectsBlankIsbn);
        failed += run("returnUnknownLoanIsError",       LibraryTest::returnUnknownLoanIsError);
        if (failed == 0) System.out.println("ALL PASS");
        else             { System.out.println(failed + " FAIL"); System.exit(1); }
    }

    interface T { void run() throws Exception; }
    static int run(String name, T t) {
        try { t.run(); System.out.println("  ok  " + name); return 0; }
        catch (Throwable e) { System.out.println("  FAIL " + name + ": " + e); return 1; }
    }

    static Library newLibrary(Clock clock) {
        return new Library(
                new InMemoryRepository<>(Book::isbn),
                new InMemoryRepository<>(Member::id),
                new InMemoryRepository<>(Loan::id),
                clock,
                3, 14, 25);
    }

    static void cannotCheckoutBookAlreadyOnLoan() {
        var lib = newLibrary(Clock.systemUTC());
        lib.addBook("1234", "Java", "Deitel");
        lib.addMember("Ada", "ada@x.com");
        lib.addMember("Bob", "bob@x.com");
        if (!lib.checkout("1234", 1L).isOk()) throw new AssertionError("first checkout should succeed");
        var r2 = lib.checkout("1234", 2L);
        if (r2.isOk()) throw new AssertionError("second checkout should fail");
        if (!r2.error().contains("already on loan")) throw new AssertionError("unexpected error: " + r2.error());
    }

    static void maxLoansPerMemberEnforced() {
        var lib = newLibrary(Clock.systemUTC());
        lib.addMember("Ada", "ada@x.com");
        for (int i = 0; i < 3; i++) {
            lib.addBook("isbn-" + i, "t", "a");
            if (!lib.checkout("isbn-" + i, 1L).isOk()) throw new AssertionError("checkout " + i + " should succeed");
        }
        lib.addBook("isbn-3", "t", "a");
        var r = lib.checkout("isbn-3", 1L);
        if (r.isOk()) throw new AssertionError("4th checkout should fail");
        if (!r.error().contains("too many")) throw new AssertionError("unexpected error: " + r.error());
    }

    static void fineForOverdue() {
        var lib = newLibrary(Clock.fixed(LocalDate.of(2024, 1, 1).atStartOfDay(ZoneOffset.UTC).toInstant(), ZoneOffset.UTC));
        lib.addBook("1234", "Java", "Deitel");
        lib.addMember("Ada", "ada@x.com");
        var loan = lib.checkout("1234", 1L).orElseThrow();
        // Move clock 20 days forward.
        var later = Clock.fixed(LocalDate.of(2024, 1, 21).atStartOfDay(ZoneOffset.UTC).toInstant(), ZoneOffset.UTC);
        var lib2 = new Library(
                new InMemoryRepository<>(Book::isbn),
                new InMemoryRepository<>(Member::id),
                new InMemoryRepository<>(Loan::id),
                later, 3, 14, 25);
        // Note: in production we'd share the same loan repo. For this test, just compute fine.
        long fine = lib2.fineFor(loan);
        if (fine != 6 * 25) throw new AssertionError("fine was " + fine);
    }

    static void addBookRejectsBlankIsbn() {
        var lib = newLibrary(Clock.systemUTC());
        var r = lib.addBook("", "t", "a");
        if (r.isOk()) throw new AssertionError("blank isbn should fail");
    }

    static void returnUnknownLoanIsError() {
        var lib = newLibrary(Clock.systemUTC());
        var r = lib.returnBook(99L);
        if (r.isOk()) throw new AssertionError("returning unknown loan should fail");
    }
}
