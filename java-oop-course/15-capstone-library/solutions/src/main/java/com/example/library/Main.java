package com.example.library;

import com.example.library.model.Book;
import com.example.library.model.Loan;
import com.example.library.model.Member;
import com.example.library.service.InMemoryRepository;
import com.example.library.service.Library;
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
            System.out.println("Library CLI — type 'help' for commands, 'quit' to exit");
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
                System.out.println(r.isOk() ? "OK: " + r.orElseThrow() : "ERROR: " + r.error());
            }
            case "book" -> {
                var fields = parts[1].split("\\s+", 3);
                var r = lib.addBook(fields[0], fields[1], fields[2]);
                System.out.println(r.isOk() ? "OK: " + r.orElseThrow() : "ERROR: " + r.error());
            }
            default -> System.out.println("add what?");
        }
    }

    static void handleCheckout(Library lib, String rest) {
        var fields = rest.split("\\s+");
        var r = lib.checkout(fields[0], Long.parseLong(fields[1]));
        System.out.println(r.isOk() ? "OK: loan " + r.orElseThrow().id() : "ERROR: " + r.error());
    }

    static void handleReturn(Library lib, String rest) {
        var r = lib.returnBook(Long.parseLong(rest));
        System.out.println(r.isOk() ? "OK: returned loan " + r.orElseThrow().id() : "ERROR: " + r.error());
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
