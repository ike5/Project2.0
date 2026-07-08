# Challenge 08 — Reference Solution

### 1. Cross-user edit
```java
@Test
void update_byNonOwner_returns403() throws Exception {
    when(service.update(eq(1L), any(), any(), anyBoolean(), eq(42L)))
        .thenThrow(new ForbiddenException("not your task"));

    mvc.perform(put("/api/tasks/1")
            .with(jwt().jwt(j -> j.subject("42")))
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"title\":\"hacked\"}"))
       .andExpect(status().isForbidden())
       .andExpect(jsonPath("$.type").value(org.hamcrest.Matchers.containsString("forbidden")));
}
```

### 2. Validation problem detail
```java
@Test
void create_withBlankTitle_returnsProblemDetail() throws Exception {
    mvc.perform(post("/api/tasks")
            .with(jwt().jwt(j -> j.subject("42")))
            .contentType(MediaType.APPLICATION_JSON)
            .content("{\"title\":\"\"}"))
       .andExpect(status().isBadRequest())
       .andExpect(jsonPath("$.type").value(containsString("validation")))
       .andExpect(jsonPath("$.errors[0].field").value("title"));
}
```

### 3. DB constraint
```java
@DataJpaTest
@AutoConfigureTestDatabase(replace = AutoConfigureTestDatabase.Replace.NONE)
@Testcontainers
class AppUserRepositoryIT {
    @Container static PostgreSQLContainer<?> pg = new PostgreSQLContainer<>("postgres:16");
    @DynamicPropertySource static void p(DynamicPropertyRegistry r) {
        r.add("spring.datasource.url", pg::getJdbcUrl);
        r.add("spring.datasource.username", pg::getUsername);
        r.add("spring.datasource.password", pg::getPassword);
    }
    @Autowired AppUserRepository repo;

    @Test
    void duplicateEmail_isRejectedByDb() {
        repo.save(new AppUser("a@x.com", "a1", "hash", Role.USER));
        assertThatThrownBy(() -> {
            repo.saveAndFlush(new AppUser("a@x.com", "a2", "hash", Role.USER));
        }).isInstanceOf(DataIntegrityViolationException.class);
    }
}
```

### 4. Parametrized
```java
@ParameterizedTest
@CsvSource({
    ",       missing title",   // empty input
    "a,      ok",              // valid
    "'   ',  missing title"    // blank
})
void create_validatesTitle(String title, String expected) {
    if ("ok".equals(expected)) {
        // assert it doesn't throw
    } else {
        assertThatThrownBy(() -> service.create(title, "...", 1L))
            .isInstanceOf(IllegalArgumentException.class)
            .hasMessageContaining("title");
    }
}
```

### 5. Testcontainers Redis + Kafka
```java
@Testcontainers
class CacheAndMessagingIT {
    @Container static GenericContainer<?> redis = new GenericContainer<>("redis:7").withExposedPorts(6379);
    @Container static KafkaContainer kafka = new KafkaContainer(DockerImageName.parse("confluentinc/cp-kafka:7.6.0"));

    @DynamicPropertySource static void p(DynamicPropertyRegistry r) {
        r.add("spring.data.redis.host", redis::getHost);
        r.add("spring.data.redis.port", () -> redis.getMappedPort(6379));
        r.add("spring.kafka.bootstrap-servers", kafka::getBootstrapServers);
    }

    @Autowired RedisTemplate<String, String> redis;
    @Autowired KafkaTemplate<String, String> kafka;

    @Test
    void redisRoundTrip() {
        redis.opsForValue().set("k", "v");
        assertThat(redis.opsForValue().get("k")).isEqualTo("v");
    }

    @Test
    void kafkaRoundTrip() {
        kafka.send("test", "hello");
        // a @KafkaListener(topics="test") consumer logs receipt
    }
}
```

### 6. Contract test (stretch)
```xml
<dependency>
  <groupId>org.springframework.cloud</groupId>
  <artifactId>spring-cloud-starter-contract-verifier</artifactId>
  <scope>test</scope>
</dependency>
```
```groovy
// src/test/resources/contracts/taskCreated.groovy
Contract.make {
    request { method 'POST'; url '/api/tasks'; body(title: "buy milk") }
    response {
        status 201
        headers { header 'Location': '/api/tasks/1' }
        body(id: 1, title: "buy milk", done: false)
    }
}
```
`mvn verify` generates a stub the consumer can `@Autowired`, asserting the
shape matches the recorded contract.

> Contract tests catch breaking changes **at build time** — before the
> client app even tries to call the new version of the server.
