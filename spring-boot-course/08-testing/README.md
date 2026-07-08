# Module 08 — Testing (Unit, Slice, Integration)

**Goal:** write tests that are **fast, focused, and trustworthy** — the kind
you can run on every save and trust to catch real bugs. You'll master
three layers (unit, slice, integration), learn the **Testcontainers** pattern
for real-database tests, and end the module with a coverage report that
proves your service is exercised end-to-end.

⏱️ ~3 hours · 🎯 Prereq: Modules 02–07 complete (auth + JPA + controllers).

> Tests are not a separate phase of the project — they are part of every
> module from here on. Module 08 gives you the *vocabulary*; every later
> module asks you to test what you build.

---

## 1. The test pyramid

```
            ╱  ╲           E2E (rare, slow, brittle)
           ╱    ╲
          ╱──────╲         Integration: full Spring context
         ╱        ╲
        ╱──────────╲       Slice: @WebMvcTest, @DataJpaTest (fast, focused)
       ╱            ╲
      ╱──────────────╲     Unit: pure JUnit + Mockito (microseconds)
```

| Layer | Speed | What it tests | Tool |
|-------|-------|--------------|------|
| **Unit** | <10 ms | A class in isolation | JUnit 5 + Mockito + AssertJ |
| **Slice** | <1 s | One layer (web, JPA, JSON) | `@WebMvcTest`, `@DataJpaTest` |
| **Integration** | 5–30 s | The whole app + real DB | `@SpringBootTest` + Testcontainers |
| **E2E** | minutes | The system as a user would | Selenium, Playwright, etc. (out of scope) |

> **Rule of thumb:** thousands of unit tests, hundreds of slice tests, a few
> dozen integration tests, a handful of E2E.

---

## 2. The starter

`spring-boot-starter-test` is already in `pom.xml` from the generated
project. It brings:

- **JUnit 5** — the test framework.
- **Mockito** — mocking.
- **AssertJ** — fluent assertions.
- **Spring Test** — `@SpringBootTest`, `MockMvc`, etc.
- **JsonPath** — JSON assertions in MockMvc.
- **Hamcrest** — matchers (legacy; prefer AssertJ).

---

## 3. The pattern: AAA (Arrange, Act, Assert)

Every test reads the same:

```java
@Test
void markDone_flipsFlagAndPreservesId() {
    // Arrange
    var repo = mock(TaskRepository.class);
    var svc  = new TaskService(repo);
    var existing = new Task(1L, "buy milk", "...", false, Instant.now());
    when(repo.findById(1L)).thenReturn(Optional.of(existing));
    when(repo.save(any())).thenAnswer(inv -> inv.getArgument(0));

    // Act
    var updated = svc.markDone(1L);

    // Assert
    assertThat(updated.getId()).isEqualTo(1L);
    assertThat(updated.isDone()).isTrue();
    verify(repo).save(any(Task.class));
}
```

---

## 4. Mockito essentials

```java
// create
var repo = mock(TaskRepository.class);
var svc  = new TaskService(repo);                  // constructor injection

// stub
when(repo.findById(1L)).thenReturn(Optional.of(task));
when(repo.findById(99L)).thenReturn(Optional.empty());
when(repo.save(any())).thenAnswer(inv -> inv.getArgument(0));

// verify
verify(repo).findById(1L);
verify(repo, never()).deleteById(any());
verify(repo, times(2)).save(any());

// argument captors
ArgumentCaptor<Task> captor = ArgumentCaptor.forClass(Task.class);
verify(repo).save(captor.capture());
assertThat(captor.getValue().getTitle()).isEqualTo("buy milk");

// exception
when(repo.findById(99L)).thenThrow(new RuntimeException("db down"));
```

> **`@Mock` and `@InjectMocks`** — Spring's test support wires these for you:
> ```java
> @ExtendWith(MockitoExtension.class)
> class TaskServiceTest {
>     @Mock TaskRepository repo;
>     @InjectMocks TaskService service;
>     // ...
> }
> ```

---

## 5. AssertJ — fluent assertions that read like English

```java
assertThat(tasks).hasSize(3)
                 .extracting(Task::getTitle)
                 .containsExactly("a", "b", "c");

assertThat(task).isNotNull()
                .hasFieldOrPropertyWithValue("done", true);

assertThatThrownBy(() -> service.get(99L))
    .isInstanceOf(NotFoundException.class)
    .hasMessageContaining("not found");
```

---

## 6. `@WebMvcTest` — controller tests without a DB

Slice test for the web layer. Loads only Spring MVC, your controllers, the
filter chain. The data layer is mocked.

```java
@WebMvcTest(TaskController.class)
class TaskControllerTest {

    @Autowired MockMvc mvc;
    @MockBean TaskService service;

    @Test
    void get_returnsTask() throws Exception {
        var task = new Task(1L, "buy milk", "2%", false, Instant.parse("2024-01-15T10:00:00Z"));
        when(service.get(1L)).thenReturn(task);

        mvc.perform(get("/api/tasks/1"))
           .andExpect(status().isOk())
           .andExpect(jsonPath("$.title").value("buy milk"))
           .andExpect(jsonPath("$.done").value(false));
    }

    @Test
    void create_returns201AndBody() throws Exception {
        var saved = new Task(1L, "buy milk", "2%", false, Instant.now());
        when(service.create(eq("buy milk"), eq("2%"), any())).thenReturn(saved);

        mvc.perform(post("/api/tasks")
                .with(jwt())                                 // bypass JWT filter
                .contentType(MediaType.APPLICATION_JSON)
                .content("""
                    {"title":"buy milk","description":"2%"}"""))
           .andExpect(status().isCreated())
           .andExpect(header().string("Location", "/api/tasks/1"));
    }
}
```

> **`@MockBean`** (Spring 6.2+ also supports the standard `@MockitoBean`) —
> it swaps the real `TaskService` for a Mockito mock inside the slice
> context.

**Bypassing security in tests:** `.with(jwt())` (from
`org.springframework.security.test.web.servlet.request.SecurityMockMvcRequestPostProcessors`)
puts a fake authenticated principal on the request — no need to issue a real
JWT in slice tests.

---

## 7. `@DataJpaTest` — JPA tests with an in-memory or testcontainer DB

```java
@DataJpaTest
@Testcontainers
class TaskRepositoryTest {

    @Container
    static PostgreSQLContainer<?> postgres = new PostgreSQLContainer<>("postgres:16");

    @DynamicPropertySource
    static void datasource(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url",  postgres::getJdbcUrl);
        r.add("spring.datasource.username", postgres::getUsername);
        r.add("spring.datasource.password", postgres::getPassword);
    }

    @Autowired TaskRepository repo;
    @Autowired TestEntityManager em;

    @Test
    void findByDone_returnsOnlyMatching() {
        em.persist(new Task("a", "..."));
        em.persist(new Task("b", "..."));
        em.flush();

        var open = repo.findByDone(false);
        assertThat(open).hasSize(2);
    }
}
```

> **`Testcontainers`** spins up a real Postgres in Docker for the test. The
> data is real, the SQL is real, the constraints fire. This is the **only
> reliable way to test JPA code** — H2 lies about things like `ON DELETE
> CASCADE`, full-text search, and Postgres-specific types.

By default `@DataJpaTest` uses H2. Override with `@AutoConfigureTestDatabase(replace = NONE)`
to disable the H2 substitution and use the Testcontainer instead — or just
set the datasource properties as above.

---

## 8. `@SpringBootTest` — the full context

Use sparingly. It boots the whole app, including security, Flyway, and any
auto-config.

```java
@SpringBootTest(webEnvironment = SpringBootTest.WebEnvironment.RANDOM_PORT)
class TaskApiIT {

    @LocalServerPort int port;
    @Autowired TestRestTemplate rest;

    @Test
    void fullRoundTrip() {
        var reg = new RegisterRequest("ann@example.com", "ann", "password123");
        var auth = rest.postForObject("http://localhost:" + port + "/api/auth/register",
            reg, AuthResponse.class);
        var headers = new HttpHeaders();
        headers.setBearerAuth(auth.accessToken());
        headers.setContentType(MediaType.APPLICATION_JSON);

        var create = new HttpEntity<>("""
            {"title":"buy milk","description":"2%"}""", headers);
        var resp = rest.exchange("http://localhost:" + port + "/api/tasks",
            HttpMethod.POST, create, TaskResponse.class);
        assertThat(resp.getStatusCode()).isEqualTo(HttpStatus.CREATED);
        assertThat(resp.getBody().title()).isEqualTo("buy milk");
    }
}
```

For the database, pair with Testcontainers exactly like `@DataJpaTest`.

---

## 9. Test isolation and `@Transactional`

By default, `@DataJpaTest` wraps each test in a transaction that's rolled
back at the end. That means tests don't pollute each other — but it also
means **you can't test code that runs in a separate transaction** (because
it can't see uncommitted rows).

For `@SpringBootTest`, you can use:

```java
@SpringBootTest
@AutoConfigureMockMvc
@ActiveProfiles("test")
@Testcontainers
class TaskApiIT { ... }
```

…with a Testcontainer Postgres whose state persists between tests. Clean
up in `@AfterEach` if you need to.

> **Pro tip:** use **distinct database per test class** to avoid ordering
> bugs. Each `Testcontainer` is a fresh container; each `@DataJpaTest`
> rolls back. Both are sufficient.

---

## 10. Code coverage — the JaCoCo Maven plugin

Add to `pom.xml`:
```xml
<plugin>
  <groupId>org.jacoco</groupId>
  <artifactId>jacoco-maven-plugin</artifactId>
  <version>0.8.12</version>
  <executions>
    <execution>
      <goals><goal>prepare-agent</goal></goals>
    </execution>
    <execution>
      <id>report</id>
      <phase>test</phase>
      <goals><goal>report</goal></goals>
    </execution>
  </executions>
</plugin>
```

Run: `mvn test` then open `target/site/jacoco/index.html`.

> Coverage is a *signal*, not a goal. 100% coverage with bad tests is
> worse than 70% coverage with focused tests on the critical paths.

---

## 11. Common testing pitfalls

| Symptom | Cause | Fix |
|---------|-------|-----|
| `NoSuchBeanDefinitionException` in `@WebMvcTest` | Filter or security config not loaded | Add `@Import(SecurityConfig.class)` or use `@AutoConfigureMockMvc` with `.with(jwt())` |
| Tests pass in IDE, fail in CI | Hidden dependency on local Postgres | Use Testcontainers |
| `@MockBean` does nothing | Class is the wrong one (subclass vs interface) | Mock the type the controller injects |
| `LazyInitializationException` in test | `open-in-view` is off and you touched a lazy field outside `@Transactional` | Use a service method, or `@Transactional` on the test |
| `BeanCreationException` because of a missing bean | A real production bean is needed by something you imported | Use `@SpringBootTest` for that one, or `@Import` the missing config |
| Tests are slow | Lots of `@SpringBootTest` | Prefer `@WebMvcTest` / `@DataJpaTest` |

---

## 12. Do the lab

Write tests at three levels for `taskforge`: unit tests for the service,
slice tests for the controller, and a Testcontainer-backed JPA test. Then
generate a coverage report.

👉 **[lab.md](./lab.md)**

Then test yourself: 👉 **[challenge.md](./challenge.md)**

---

## Key terms (see [GLOSSARY](../GLOSSARY.md))

JUnit 5 · Mockito · AssertJ · AAA · `@WebMvcTest` · `@DataJpaTest` · `@SpringBootTest` · `MockMvc` · `TestRestTemplate` · `@MockBean` · Testcontainers · `@Container` · `@DynamicPropertySource` · JaCoCo

**Next →** [Module 09: Logging, Configuration & Profiles](../09-logging-config-profiles/)
