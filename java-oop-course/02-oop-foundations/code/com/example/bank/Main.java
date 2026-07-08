package com.example.bank;

public class Main {
    public static void main(String[] args) {
        var a = BankAccount.open("Ada");
        a.deposit(10_00);
        a.withdraw(3_50);
        System.out.println(a);

        var b = BankAccount.open("Grace");
        b.deposit(50_00);
        System.out.println(b);

        try { a.withdraw(999_00); }
        catch (IllegalStateException e) { System.out.println("rejected: " + e.getMessage()); }

        try { BankAccount.open(null); }
        catch (NullPointerException e) { System.out.println("rejected: " + e.getMessage()); }

        var a2 = BankAccount.open("Ada");
        System.out.println("a == a2: " + a.equals(a2));
        System.out.println("a == a : " + a.equals(a));
    }
}
