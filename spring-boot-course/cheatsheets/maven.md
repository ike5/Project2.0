# Cheatsheet — Maven

Quick reference for the build tool. Keep it open while you build.

## The three commands you'll run 100×

```bash
mvn spring-boot:run       # dev (recompiles + restarts)
mvn -q test               # run tests
mvn -q -DskipTests package # build the JAR
mvn -q dependency:tree    # see the resolved dep graph
```

## `pom.xml` skeleton

```xml
<?xml version="1.0" encoding="UTF-8"?>
<project xmlns="http://maven.apache.org/POM/4.0.0">
  <modelVersion>4.0.0</modelVersion>

  <parent>
    <groupId>org.springframework.boot</groupId>
    <artifactId>spring-boot-starter-parent</artifactId>
    <version>3.3.4</version>
  </parent>

  <groupId>com.taskforge</groupId>
  <artifactId>taskforge</artifactId>
  <version>0.0.1-SNAPSHOT</version>
  <name>taskforge</name>

  <properties>
    <java.version>21</java.version>
    <project.build.sourceEncoding>UTF-8</project.build.sourceEncoding>
  </properties>

  <dependencies>
    <!-- ... -->
  </dependencies>

  <build>
    <plugins>
      <!-- ... -->
    </plugins>
  </build>
</project>
```

## Useful plugins

```xml
<!-- Spring Boot: build the fat JAR -->
<plugin>
  <groupId>org.springframework.boot</groupId>
  <artifactId>spring-boot-maven-plugin</artifactId>
</plugin>

<!-- Surefire: unit tests (*Test.java) -->
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-surefire-plugin</artifactId>
</plugin>

<!-- Failsafe: integration tests (*IT.java) -->
<plugin>
  <groupId>org.apache.maven.plugins</groupId>
  <artifactId>maven-failsafe-plugin</artifactId>
  <executions>
    <execution>
      <goals>
        <goal>integration-test</goal>
        <goal>verify</goal>
      </goals>
    </execution>
  </executions>
</plugin>

<!-- JaCoCo: code coverage -->
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.12</version>
  <executions>
    <execution><goals><goal>prepare-agent</goal></goals></execution>
    <execution>
      <id>report</id>
      <phase>test</phase>
      <goals><goal>report</goal></goals>
    </execution>
  </executions>
</plugin>
```

## Profiles

```xml
<profiles>
  <profile>
    <id>prod</id>
    <build>
      <plugins>
        <plugin>
          <groupId>org.springframework.boot</groupId>
          <artifactId>spring-boot-maven-plugin</artifactId>
          <configuration>
            <excludes>
              <exclude>
                <groupId>org.projectlombok</groupId>
                <artifactId>lombok</artifactId>
              </exclude>
            </excludes>
          </configuration>
        </plugin>
      </plugins>
    </build>
  </profile>
</profiles>
```

```bash
mvn -Pprod package       # activate
mvn -P-prod package      # deactivate
```

## The dependency tree (your best debugging tool)

```bash
mvn -q dependency:tree
# com.taskforge:taskforge:jar:0.0.1-SNAPSHOT
# ├─ org.springframework.boot:spring-boot-starter-web:jar:3.3.4
# │  ├─ org.springframework.boot:spring-boot-starter-json:jar:3.3.4
# │  │  └─ com.fasterxml.jackson.core:jackson-databind:jar:2.17.2
# │  └─ org.springframework.boot:spring-boot-starter-tomcat:jar:3.3.4
# │     └─ org.apache.tomcat.embed:tomcat-embed-core:jar:10.1.30
# ...

mvn -q dependency:tree -Dincludes=org.springframework:*   # filter
mvn -q dependency:tree -Dverbose                         # see conflicts
mvn -q dependency:resolve                                # download only
```

## Useful flags

```bash
-DskipTests              # skip all tests
-Dmaven.test.skip=true   # skip compilation too
-Dspring.profiles.active=prod
-Dspring-boot.run.arguments="--server.port=9090"
-o                       # offline
-U                       # update snapshots
-e -X                    # error + debug logging
-q                       # quiet
```

## Common pitfalls

- **"Failed to read artifact descriptor"** — your local repo is stale or
  the dep isn't there. `mvn -U dependency:resolve`.
- **Version conflicts** — `mvn dependency:tree -Dverbose | grep conflict`
  shows them. Add an explicit `<dependency>` with the version you want.
- **`mvn spring-boot:run` doesn't see changes** — your IDE's compile
  might be off. Run `mvn compile` and restart.
- **The JAR doesn't have a `Main-Class`** — the
  `spring-boot-maven-plugin` repackager is what adds it. `mvn package`,
  not `mvn jar:jar`.
- **`-DskipTests` skips compile too in older versions** — use
  `-Dtest=NoSuchTest` or `-DfailIfNoTests=false` instead.

## Multi-module projects (preview)

```xml
<modules>
  <module>taskforge-api</module>
  <module>taskforge-worker</module>
  <module>taskforge-events</module>  <!-- shared DTOs -->
</modules>
```

```bash
mvn -pl taskforge-api -am package   # build api + its dependencies
mvn -pl taskforge-worker -am spring-boot:run
```

> Module 11's challenge is the natural starting point for a multi-module
> project.
