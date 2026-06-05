namespace TaskApi.Dtos;

// DTOs (data transfer objects) shape the API's request/response bodies, decoupled
// from the EF entity. Records give concise, immutable payloads.

public record CreateTaskDto(string Title);

public record TaskDto(int Id, string Title, bool IsDone, DateTime CreatedAt, DateTime? CompletedAt);
