package com.example.plugins;

import java.util.List;

public class Main {
    public static void main(String[] args) throws Exception {
        var service = new Service();
        Processor.run(service);

        var banner = """
                +--------------------+
                |  Annotation runner |
                +--------------------+""";
        System.out.println(banner);

        var a = 42;
        var b = 42L;
        var c = 3.14;
        var d = "hi";
        var e = List.of(1, 2);
        System.out.println(a + " " + b + " " + c + " " + d + " " + e);
    }
}
