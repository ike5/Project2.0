package com.example.parser;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.util.OptionalInt;
import java.util.Properties;

public class Main {
    public static void main(String[] args) throws IOException {
        for (String s : new String[]{"42", "  7  ", "oops", null}) {
            OptionalInt v = IntParser.tryParse(s);
            System.out.println("tryParse(\"" + s + "\") = " +
                    (v.isPresent() ? v.getAsInt() : "<empty>"));
        }
        try { IntParser.parseOrThrow("not a number"); }
        catch (IllegalArgumentException e) { System.out.println("rejected: " + e.getMessage()); }

        Path src = Path.of("/tmp/oop08-src.txt");
        Path dst = Path.of("/tmp/oop08-dst.txt");
        Files.writeString(src, "Hello, exceptions!");
        long n = FileCopier.copy(src, dst);
        System.out.println("copied " + n + " bytes; dst says: " + Files.readString(dst));

        var props = new Properties();
        props.setProperty("port", "8080");
        var cfg = new ConfigService(props);
        try { System.out.println("port: " + cfg.requireInt("port")); }
        catch (ServiceException e) { System.out.println("rejected: " + e.getMessage()); }
        try { System.out.println("host: " + cfg.requireInt("host")); }
        catch (ServiceException e) { System.out.println("rejected: " + e.getMessage()); }
    }
}
