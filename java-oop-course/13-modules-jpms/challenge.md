# Challenge 13 — Modules (JPMS) & Packaging

Solution in [`solutions/`](./solutions/). Try first.

## Tasks

1. **Three modules: `util`, `core`, `app`.** Build
   - `com.example.util` exports a `Strings` utility class.
   - `com.example.core` requires `com.example.util`, exports a
     `Greeter` that uses `Strings`.
   - `com.example.app` requires `com.example.core` (and transitively
     `util` via `requires transitive`), runs a `Main`.
   Confirm that `app` cannot `import com.example.util.X` if `X` is not
   in an `exports`ed package.

2. **A service provider.** Define `com.example.spi.PaymentProcessor`
   with a `String charge(String account, long cents)`. Provide two
   providers in two modules (`stripe` and `paypal`). The `app` module
   uses `ServiceLoader<PaymentProcessor>` to discover them and runs each
   one. Show that the providers can be swapped by changing the
   `--module-path`.

3. **A custom JRE with `jlink`.** Build a custom JRE for your three-
   module app from task 1. Confirm it's smaller than the full JDK
   (`du -sh custom-jre`).

4. **An `opens` package for Jackson.** Add Jackson to your
   `--module-path` (it's a modular JAR in 2.13+) and add
   `opens com.example.app.model to com.fasterxml.jackson.databind;` to
   your `app`'s `module-info`. Confirm that without the `opens`, the
   reflection fails with `InvalidModuleDescriptorException` or
   similar.

5. **`jpackage` an application image.** Use `jpackage --type
   app-image` to build a folder with a launcher for your app. Run the
   launcher.

## Success criteria

- [ ] The three modules compile and run with `java --module-path ...`.
- [ ] The service providers are discovered via `ServiceLoader`.
- [ ] The custom JRE is noticeably smaller than the full JDK.
- [ ] Without `opens`, the reflection fails; with `opens`, it works.
- [ ] `jpackage` produces a runnable application image.
