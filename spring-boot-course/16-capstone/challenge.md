# Challenge 16 — Beyond the Course

There's no reference solution. The "solution" is the system you've built.

That said, here are the **natural extensions** the course leaves to you —
they're the projects a real Spring Boot developer tackles in their first
year on the job. Pick one; do it; you'll learn more from finishing it
than from any module.

## Tier 1 — Within a week

- **Spring Cloud Config** — move all `application.yml` to a central
  config server. The `taskforge` clients become thin and configuration
  changes roll out without a redeploy.
- **Resilience4j circuit breakers** — wrap the MinIO presign call and
  the Kafka send. Confirm the system stays up when a dependency is slow
  or down.
- **Multi-tenancy** — add a `tenant_id` column to every table; enforce
  it in every query via a Hibernate filter. This is *the* classic Spring
  Boot refactor.

## Tier 2 — Within a month

- **Kubernetes deployment** — turn the `docker-compose.yml` into
  `Deployment`, `Service`, `Ingress`, `ConfigMap`, and `Secret`
  manifests. Add a Helm chart. The patterns are the same as the
  `slack-clone-course`'s Kubernetes module.
- **OAuth2 / OIDC provider** — replace the HS256 JWT with an asymmetric
  key pair, expose a JWKS endpoint, and validate tokens from an external
  IdP (Keycloak, Auth0, Cognito).
- **Event sourcing** — model `Task` as a stream of `TaskCreated`,
  `TaskUpdated`, `TaskCompleted` events, and project the current state.
  The Kafka foundation you built in Module 11 is the substrate.

## Tier 3 — Career-defining

- **Modulith migration** — split `taskforge` into Spring Modulith
  modules (`task`, `auth`, `attachments`, `notifications`) with
  package-private boundaries verified at build time. The testing
  patterns you learned keep paying off.
- **Native image with GraalVM** — `mvn -Pnative native:compile`. Startup
  drops to ~50 ms, memory to ~50 MB. Same code, different runtime.
- **Distributed transactions** — implement the **Saga pattern** for a
  multi-service workflow. Module 11's events are the message channel.
  This is the hardest problem in microservices; doing it once makes you
  understand every distributed-systems paper.

## The meta-lesson

Every one of these is **"the same pattern, applied to a harder
problem"**:
- **Config** — same `@ConfigurationProperties`, different source.
- **Resilience** — same `@Cacheable`, different failure mode.
- **Tenancy** — same `@Entity`, additional filter.
- **Kubernetes** — same Dockerfile, different orchestrator.
- **Native image** — same `pom.xml`, different build target.

The course gave you the **vocabulary and the patterns**. The extensions
are where you turn that into a career.
