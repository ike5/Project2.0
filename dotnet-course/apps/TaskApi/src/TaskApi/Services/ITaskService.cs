using TaskApi.Dtos;

namespace TaskApi.Services;

/// <summary>Business logic for tasks. Endpoints depend on this interface (DI + testability).</summary>
public interface ITaskService
{
    Task<IReadOnlyList<TaskDto>> GetAllAsync();
    Task<TaskDto?> GetAsync(int id);
    Task<TaskDto> CreateAsync(CreateTaskDto dto);
    Task<bool> CompleteAsync(int id);
    Task<bool> DeleteAsync(int id);
}
