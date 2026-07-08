#!/usr/bin/env bash
# Verify the Java toolchain for the course.
# Confirms java, javac, jar, jlink, JAVA_HOME, and runs a smoke test.

set -euo pipefail

ok() { printf "  \033[32m✓\033[0m %s\n" "$*"; }
fail() { printf "  \033[31m✗\033[0m %s\n" "$*"; exit 1; }
section() { printf "\n\033[1m%s\033[0m\n" "$*"; }

section "1. Toolchain"

command -v java  >/dev/null 2>&1 || fail "java not found on PATH"
ok "java on PATH: $(command -v java)"

command -v javac >/dev/null 2>&1 || fail "javac not found on PATH (install JDK 21)"
ok "javac on PATH: $(command -v javac)"

command -v jar   >/dev/null 2>&1 || fail "jar not found on PATH"
ok "jar on PATH: $(command -v jar)"

command -v jlink >/dev/null 2>&1 || fail "jlink not found (you need a full JDK, not a JRE)"
ok "jlink on PATH: $(command -v jlink)"

section "2. Versions"

JAVA_VERSION=$(java -version 2>&1 | head -n1 | awk -F\" '{print $2}')
ok "java reports: $JAVA_VERSION"

# Course standard is 21; warn but don't fail on 17+ (also LTS).
MAJOR=$(echo "$JAVA_VERSION" | awk -F. '{print $1}')
if [ "$MAJOR" -lt 17 ]; then
  fail "Java $MAJOR is too old. The course needs Java 17 minimum (Java 21 recommended)."
fi
if [ "$MAJOR" -lt 21 ]; then
  printf "  \033[33m!\033[0m %s\n" "Java $MAJOR works for most modules; some 21-only features may not be available."
fi

JAVAC_VERSION=$(javac -version 2>&1 | awk '{print $2}')
ok "javac reports: $JAVAC_VERSION"

section "3. JAVA_HOME"

if [ -n "${JAVA_HOME:-}" ]; then
  ok "JAVA_HOME is set: $JAVA_HOME"
else
  printf "  \033[33m!\033[0m %s\n" "JAVA_HOME is not set. Many tools need it. See Module 00, Step 2."
fi

section "4. Smoke test"

WORK=$(mktemp -d)
trap 'rm -rf "$WORK"' EXIT

cat > "$WORK/Hello.java" <<'EOF'
public class Hello {
    public static void main(String[] args) {
        System.out.println("Hello, Java " + Runtime.version());
    }
}
EOF

(cd "$WORK" && javac Hello.java && java Hello) >/dev/null
ok "javac + java produce expected output"

# Confirm a record + pattern matching compile (Java 16+).
cat > "$WORK/Point.java" <<'EOF'
public class Point {
    public static void main(String[] args) {
        var p = new P(3, 4);
        System.out.println(p + " | d=" + p.dist());
    }
    record P(int x, int y) { double dist() { return Math.hypot(x, y); } }
}
EOF
(cd "$WORK" && javac Point.java && java Point) >/dev/null
ok "records + pattern matching compile"

# Module path test — Main is also modular.
mkdir -p "$WORK/jpms/src/com/example/greeter"
mkdir -p "$WORK/jpms/src-app/com/example/app"
cat > "$WORK/jpms/src/module-info.java" <<'EOF'
module com.example.greeter {
    exports com.example.greeter;
}
EOF
cat > "$WORK/jpms/src/com/example/greeter/Greeter.java" <<'EOF'
package com.example.greeter;
public class Greeter {
    public static String greet(String name) { return "Hello, " + name; }
}
EOF
cat > "$WORK/jpms/src-app/module-info.java" <<'EOF'
module com.example.app {
    requires com.example.greeter;
}
EOF
cat > "$WORK/jpms/src-app/com/example/app/Main.java" <<'EOF'
package com.example.app;
import com.example.greeter.Greeter;
public class Main {
    public static void main(String[] args) {
        System.out.println(Greeter.greet("JPMS"));
    }
}
EOF
(cd "$WORK/jpms" && \
  javac -d out src/module-info.java src/com/example/greeter/Greeter.java && \
  jar --create --file=greeter.jar --module-version=1.0 -C out . && \
  javac -d out-app -p greeter.jar src-app/module-info.java src-app/com/example/app/Main.java && \
  jar --create --file=app.jar --module-version=1.0 -C out-app . && \
  java -p greeter.jar:app.jar -m com.example.app/com.example.app.Main) >/dev/null
ok "JPMS module compile, package, and run work"

printf "\n\033[32mAll checks passed.\033[0m You are ready to start Module 01.\n"
