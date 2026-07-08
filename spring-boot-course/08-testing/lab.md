# Lab 08 — Three Layers of Tests

**You'll:** add unit tests for `TaskService`, slice tests for `TaskController`
with a fake authenticated user, and a Testcontainer-backed JPA test. Then run
`mvn test` and inspect the coverage report.

⏱️ ~60 min. Run from `spring-boot-course/apps/taskforge`. Docker must be
running (Testcontainers needs it).

---

## Part A — Unit tests for `TaskService`

`src/test/java/com/taskforge/task/TaskServiceTest.java`:
```java
package com.taskforge.task;

import com.taskforge.common.NotFoundException;
import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.extension.ExtendWith;
import org.mockito.InjectMocks;
import org.mockito.Mock;
import org.mockito.junit.jupiter.MockitoExtension;

import java.util.List;
import java.util.Optional;

import static org.assertj.core.api.Assertions.*;
import static org.mockito.ArgumentMatchers.any;
import static org.mockito.Mockito.*;

@ExtendWith(MockitoExtension.class)
class TaskServiceTest {

    @Mock TaskRepository repo;
    @InjectMocks TaskService service;

    @Test
    void create_assignsOwnerAndSaves() {
        when(repo.save(any())).thenAnswer(inv -> {
            Task t = inv.getArgument(0);
            t.setId(1L);
            return t;
        });

        Task t = service.create("buy milk", "2%", 42L);

        assertThat(t.getId()).isEqualTo(1L);
        assertThat(t.getOwnerId()).isEqualTo(42L);
        assertThat(t.isDone()).isFalse();
    }

    @Test
    void get_throwsNotFoundWhenMissing() {
        when(repo.findById(99L)).thenReturn(Optional.empty());
        assertThatThrownBy(() -> service.get(99L))
            .isInstanceOf(NotFoundException.class)
            .hasMessageContaining("99");
    }

    @Test
    void update_rejectsNonOwner() {
        var existing = new Task(1L, "buy milk", "2%", false, Instant.now());
        existing.setOwnerId(42L);
        when(repo.findById(1L)).thenReturn(Optional.of(existing));

        assertThatThrownBy(() -> service.update(1L, "hacked", null, true, 99L))
            .isInstanceOf(ForbiddenException.class);
    }

    @Test
    void delete_deletesExistingTask() {
        when(repo.existsById(1L)).thenReturn(true);
        service.delete(1L);
        verify(repo).deleteById(1L);
    }
}
```

Add the `Instant` import:
```java
import java.time.Instant;
```

Run: `mvn -q test -Dtest=TaskServiceTest`. All four pass in under 100 ms.

---

## Part B — Slice tests for `TaskController`

`src/test/java/com/taskforge/task/api/TaskControllerTest.java`:
```java
package com.taskforge.task.api;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.taskforge.task.Task;
import com.taskforge.task.TaskService;
import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.web.servlet.WebMvcTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.http.MediaType;
import org.springframework.test.web.servlet.MockMvc;

import java.time.Instant;
import java.util.List;

import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.when;
import static org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors.jwt;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

@WebMvcTest(TaskController.class)
class TaskControllerTest {

    @Autowired MockMvc mvc;
    @Autowired ObjectMapper json;
    @MockBean TaskService service;

    @Test
    void list_returnsAllTasksForUser() throws Exception {
        when(service.listForUser(42L)).thenReturn(List.of(
            new Task(1L, "a", "...", false, Instant.now()),
            new Task(2L, "b", "...", true,  Instant.now())
        ));

        mvc.perform(get("/api/tasks").with(jwt().jwt(j -> j.subject("42"))))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$[0].title").value("a"))
           .andExpect(jsonPath("$[1].done").value(true));
    }

    @Test
    void create_returns201AndBody() throws Exception {
        var saved = new Task(1L, "buy milk", "2%", false, Instant.now());
        when(service.create(eq("buy milk"), eq("2%"), any())).thenReturn(saved);

        mvc.perform(post("/api/tasks")
                .with(jwt().jwt(j -> j.subject("42")))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"title":"buy milk","description":"2%"}"""))
           .andExpect(status().isCreated())
           .andExpect(header().string("Location", "/api/tasks/1"))
           .andExpect(jsonPath("$.title").value("buy milk"));
    }

    @Test
    void create_returns400OnBlankTitle() throws Exception {
        mvc.perform(post("/api/tasks")
                .with(jwt().jwt(j -> j.subject("42")))
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"title":""}"""))
           .andExpect(status().isBadRequest())
           .andExpect(jsonPath("$.errors[0].field").value("title"));
    }

    @Test
    void unauthenticated_returns401() throws Exception {
        mvc.perform(get("/api/tasks"))
           .andExpect(status().isUnauthorized());
    }
}
```

> The `jwt().jwt(...)` post-processor sets the principal to `"42"` (a
> String) and skips the JWT filter. The controller casts
> `auth.getPrincipal()` to `Long`, so in the test we may need to adjust to
> use `Long` — see "Common pitfalls" below.

If your tests fail because the principal type is `String` instead of `Long`,
change the controller to read it differently:
```java
@GetMapping
public List<TaskResponse> list(Authentication auth) {
    Long userId = Long.valueOf(auth.getName());   // or auth.getName() if you store userId there
    return service.listForUser(userId).stream().map(TaskResponse::from).toList();
}
```

…and use `jwt().jwt(j -> j.subject("42"))` — `auth.getName()` returns
`"42"`.

Run: `mvn -q test -Dtest=TaskControllerTest`. All four pass in well under a
second.

---

## Part C — Testcontainer-backed JPA test

`src/test/java/com/taskforge/task/TaskRepositoryIT.java`:
```java
package com.taskforge.task;

import org.junit.jupiter.api.Test;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.autoconfigure.jdbc.AutoConfigureTestDatabase;
import org.springframework.boot.test.autoconfigure.orm.jpa.DataJpaTest;
import org.springframework.test.context.DynamicPropertyRegistry;
import org.springframework.test.context.DynamicPropertySource;
import org.testcontainers.containers.PostgreSQLContainer;
import org.testcontainers.junit.jupiter.Container;
import org.testcontainers.junit.jupiter.Testcontainers;

import java.util.List;

import static org.assertj.core.api.Assertions.assertThat;

@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class TaskRepositoryIT {

    @Container
    static final PostgreSQLContainer<?> postgres =
        new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void datasource(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url",      postgres::getJdbcUrl);
        r.add("spring.datasource.username", postgres::getUsername);
        r.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired TaskRepository repo;

    @Test
    void findByOwnerId_returnsOnlyOwned() {
        var t1 = repo.save(new Task("a", "..."));
        t1.setOwnerId(1L); repo.save(t1);
        var t2 = repo.save(new Task("b", "..."));
        t2.setOwnerId(2L); repo.save(t2);

        List<Task> mine = repo.findByOwnerId(1L);

        assertThat(mine).hasSize(1).first().extracting(Task::getTitle).isEqualTo("a");
    }

    @Test
    void existsByTitle_works() {
        repo.save(new Task("unique", "..."));
        // a method you'd add: boolean existsByTitle(String title);
        // assertThat(repo.existsByTitle("unique")).isTrue();
    }
}
```

Add the dependency to `pom.xml` (in `<dependencies>`, scope `test`):
```xml
<dependency>
  <groupId>org.testcontainers</groupId>
  <artifactId>postgresql</artifactId>
  <scope>test</scope>
</dependency>
```

> The IT (integration test) suffix lets Maven's `failsafe` plugin pick it up
> separately from unit tests. Add this to `pom.xml` if you want them in a
> different phase:
> ```xml
> <plugin>
>   <groupId>org.apache.maven.plugins</groupId>
>   <artifactId>maven-failsafe-plugin</artifactId>
> </plugin>
> ```

Run: `mvn -q verify`. Docker pulls `postgres:16` (one-time), starts a
container, runs Flyway + Hibernate, and the tests pass.

---

## Part D — Run all tests + coverage

Add the JaCoCo plugin (see README §10), then:
```bash
mvn -q verify
open target/site/jacoco/index.html
```

✅ **Checkpoint:** the report shows the service and controller classes at
high coverage.

---

## What you learned

- Three layers of tests: unit (Mockito, microseconds), slice (`@WebMvcTest` /
  `@DataJpaTest`, <1 s), integration (`@SpringBootTest` + Testcontainers,
  seconds).
- `MockMvc` + `jwt()` lets you test a controller without running the JWT
  filter.
- Testcontainers gives you a real Postgres in CI — no "works on my machine"
  surprises, no H2 lies about SQL behavior.
- AAA (Arrange / Act / Assert) and named tests make failures obvious.
- Coverage is a *signal*, not a goal. Aim for 70%+ on services and
  controllers, 90%+ on critical paths (auth, payments, …).

➡️ Now try the **[challenge](./challenge.md)**, then move to
[Module 09](../09-logging-config-profiles/).
