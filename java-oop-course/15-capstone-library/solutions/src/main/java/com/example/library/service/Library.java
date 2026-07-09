package com.example.library.service;

import com.example.library.model.Book;
import com.example.library.model.Loan;
import com.example.library.model.Member;
import com.example.library.util.Result;

import java.time.Clock;
import java.time.LocalDate;
import java.time.temporal.ChronoUnit;
import java.util.List;
import java.util.Objects;
import java.util.concurrent.atomic.AtomicLong;

public final class Library {
    private final Repository<Book, String>  books;
    private final Repository<Member, Long>  members;
    private final Repository<Loan, Long>   loans;
    private final Clock clock;
    private final int maxLoansPerMember;
    private final int loanDays;
    private final long centsPerDayFine;
    private final AtomicLong nextLoanId = new AtomicLong(1);
    private final AtomicLong nextMemberId = new AtomicLong(1);

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
        try {
            long id = nextMemberId.getAndIncrement();
            return members.save(new Member(id, name, email));
        } catch (Exception e) {
            return Result.err(e.getMessage());
        }
    }

    public Result<Book, String> addBook(String isbn, String title, String author) {
        try {
            return books.save(new Book(isbn, title, author));
        } catch (Exception e) {
            return Result.err(e.getMessage());
        }
    }

    public Result<Loan, String> checkout(String isbn, long memberId) {
        var book = books.findById(isbn);
        if (book.isEmpty()) return Result.err("no such book: " + isbn);
        var member = members.findById(memberId);
        if (member.isEmpty()) return Result.err("no such member: " + memberId);

        boolean alreadyLoaned = loans.findAll().stream()
                .anyMatch(l -> l.book().isbn().equals(isbn));
        if (alreadyLoaned) return Result.err("book already on loan: " + isbn);

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
        Objects.requireNonNull(loan, "loan");
        LocalDate today = LocalDate.now(clock);
        if (!today.isAfter(loan.dueOn())) return 0;
        long overdueDays = ChronoUnit.DAYS.between(loan.dueOn(), today);
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
    public List<Loan>  loans()   { return loans.findAll(); }

    public int maxLoansPerMember() { return maxLoansPerMember; }
    public int loanDays()          { return loanDays; }
    public long centsPerDayFine()  { return centsPerDayFine; }
}
