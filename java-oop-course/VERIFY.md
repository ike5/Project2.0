# VERIFY — End-to-end smoke test

Run these after Module 00 to confirm your toolchain works, and again at the
end of the course to confirm everything still does.

## 1. Toolchain present

```bash
java --version     # 21.x.x
javac --version    # 21.x.x
jar --version      # 21.x.x
jlink --version    # 21.x.x
```

You should see Java 21 (the course standard) — Java 17 LTS or 25 LTS will
also work for most modules, with notes in the text where a 21 feature is
essential (e.g. unnamed variables, scoped values).

## 2. "Hello, Java" compiles and runs

```bash
mkdir -p /tmp/java-smoke && cd /tmp/java-smoke
cat > Hello.java <<'EOF'
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello, Java " + Runtime.version());
    }
}
EOF
javac Hello.java
java Hello
```

Expected: `Hello, Java 21.x.y` (or whatever your runtime is).

## 3. A modern record compiles and runs

```bash
cat > Point.java <<'EOF'
public class Point {
    public static void main(String[] args) {
        var p = new Point2D(3, 4);
        System.out.println(p + ", distance from origin = " + p.distance());
    }
    record Point2D(int x, int y) {
        double distance() { return Math.hypot(x, y); }
    }
}
EOF
javac Point.java
java Point
```

Expected: `Point[x=3, y=4], distance from origin = 5.0` — confirms records,
text-block-free string concatenation, and `Math` work.

## 4. A simple generic class compiles and runs

```bash
cat > Box.java <<'EOF'
public class Box {
    public static void main(String[] args) {
        var b = new Box<String>();
        b.set("hi");
        System.out.println(b.get());
    }
    static class Box<T> {
        private T value;
        void set(T v) { this.value = v; }
        T get() { return value; }
    }
}
EOF
javac Box.java
java Box
```

Expected: `hi`. Confirms generics are working.

## 5. A JPMS module compiles and runs

```bash
rm -rf /tmp/jpms-smoke && mkdir -p /tmp/jpms-smoke/src/com.example.greeter
cd /tmp/jpms-smoke
cat > src/module-info.java <<'EOF'
module com.example.greeter {
    exports com.example.greeter;
}
EOF
cat > src/com.example.greeter/Greeter.java <<'EOF'
package com.example.greeter;
public class Greeter {
    public static String greet(String name) { return "Hello, " + name; }
}
EOF
cat > Main.java <<'EOF'
import com.example.greeter.Greeter;
public class Main {
    public static void main(String[] args) {
        System.out.println(Greeter.greet("Java"));
    }
}
EOF

javac -d out src/module-info.java src/com/example/greeter/Greeter.java
jar --create --file=greeter.jar --module-version=1.0 -C out .
javac -p greeter.jar Main.java
java -p greeter.jar:. Main
```

Expected: `Hello, Java`. Confirms `module-info.java`, the module path, and
modular JARs work.

## 6. The capstone compiles and tests

```bash
cd java-oop-course/15-capstone-library
# (or wherever you've kept the capstone; see that module's README)
./gradlew build    # or: mvn -B verify
```

Expected: `BUILD SUCCESSFUL` with all tests green.

---

**If any of the above fails,** see the *Troubleshooting* section in
[Module 00](./00-setup/README.md) — most issues are a missing `JAVA_HOME` or
an older JDK in `PATH`.
