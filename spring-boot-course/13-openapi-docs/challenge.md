# Challenge 13 — The Spec as a Contract

No step-by-step this time. Use what you learned. Reference solutions are in
[`solutions/`](./solutions/) — try first!

## Tasks

1. **Group your APIs.** Add `GroupedOpenApi` beans for `public` (auth,
   health) and `private` (tasks, attachments, events). Reload Swagger UI
   and confirm the dropdown switches between them.

2. **Generate a TypeScript client.** Use `openapi-generator-cli` to
   generate a TS client from `/v3/api-docs`. Import it into a tiny Node
   script and call `createTask(...)` against your running server.

3. **Pin the spec.** Save `/v3/api-docs` to `src/test/resources/openapi.json`.
   Add a test that reads the live spec and asserts it matches the file
   (`JsonNode.equals(...)`). The test fails when the API changes
   unintentionally.

4. **Document security requirements.** Add `@SecurityRequirement` to the
   controllers that need it, and `@SecurityRequirements()` (clears) on
   the auth controller. Confirm the UI shows the right padlock per
   operation.

5. **Custom `error` schema.** Add a `ProblemDetail` schema to
   `OpenApiConfig.components` and reference it from every
   `@ApiResponse(responseCode = "4xx/5xx")`. Reuse it across controllers.

6. **Stretch:** Use **Swagger Codegen** to generate a Spring Boot server
   stub from the spec. Run it; confirm it implements the same contract.
   This is the consumer-driven contract workflow — useful for proving
   your spec is implementable.

## Success criteria

- [ ] The Swagger UI has a `public` and `private` group.
- [ ] A generated TS client compiles and calls a real endpoint.
- [ ] A test compares the live spec to a checked-in baseline.
- [ ] Security requirements show the right padlock per operation.
- [ ] `ProblemDetail` is referenced from error responses.
- [ ] Stretch: a generated server stub runs.
