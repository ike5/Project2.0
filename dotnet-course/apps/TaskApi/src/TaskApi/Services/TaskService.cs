using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging;
using TaskApi.Data;
using TaskApi.Dtos;
using TaskApi.Models;

namespace TaskApi.Services;

public class TaskService(TaskDbContext db, ILogger<TaskService> logger) : ITaskService
{
    public async Task<IReadOnlyList<TaskDto>> GetAllAsync()
    {
        // Materialize the entities first, THEN map — keeps the SQL query simple and
        // avoids "could not be translated" errors from projecting via a method.
        var items = await db.Tasks.OrderBy(t => t.Id).ToListAsync();
        return items.Select(ToDto).ToList();
    }

    public async Task<TaskDto?> GetAsync(int id)
    {
        var item = await db.Tasks.FindAsync(id);
        return item is null ? null : ToDto(item);
    }

    public async Task<TaskDto> CreateAsync(CreateTaskDto dto)
    {
        if (string.IsNullOrWhiteSpace(dto.Title))
            throw new ArgumentException("Title is required", nameof(dto));

        var item = new TaskItem { Title = dto.Title.Trim() };
        db.Tasks.Add(item);
        await db.SaveChangesAsync();
        logger.LogInformation("Created task {TaskId} {Title}", item.Id, item.Title);
        return ToDto(item);
    }

    public async Task<bool> CompleteAsync(int id)
    {
        var item = await db.Tasks.FindAsync(id);
        if (item is null)
        {
            logger.LogWarning("Complete requested for missing task {TaskId}", id);
            return false;
        }
        item.IsDone = true;
        item.CompletedAt = DateTime.UtcNow;
        await db.SaveChangesAsync();
        return true;
    }

    public async Task<bool> DeleteAsync(int id)
    {
        var item = await db.Tasks.FindAsync(id);
        if (item is null) return false;
        db.Tasks.Remove(item);
        await db.SaveChangesAsync();
        return true;
    }

    private static TaskDto ToDto(TaskItem t) =>
        new(t.Id, t.Title, t.IsDone, t.CreatedAt, t.CompletedAt);
}
