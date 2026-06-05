namespace TaskApi.Models;

/// <summary>An entity mapped to the Tasks table by EF Core.</summary>
public class TaskItem
{
    public int Id { get; set; }
    public string Title { get; set; } = "";
    public bool IsDone { get; set; }
    public DateTime CreatedAt { get; set; } = DateTime.UtcNow;
    public DateTime? CompletedAt { get; set; }
}
