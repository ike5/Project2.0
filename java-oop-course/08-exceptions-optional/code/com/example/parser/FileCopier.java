package com.example.parser;

import java.io.IOException;
import java.io.InputStream;
import java.io.OutputStream;
import java.nio.file.Files;
import java.nio.file.Path;

public final class FileCopier {
    private FileCopier() {}

    public static long copy(Path source, Path target) throws IOException {
        try (InputStream  in  = Files.newInputStream(source);
             OutputStream out = Files.newOutputStream(target)) {
            return in.transferTo(out);
        }
    }
}
