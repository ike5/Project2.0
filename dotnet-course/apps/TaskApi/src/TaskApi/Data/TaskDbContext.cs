using Microsoft.EntityFrameworkCore;
using TaskApi.Models;

namespace TaskApi.Data;

/// <summary>The EF Core session with the database. One DbSet per table.</summary>
public class TaskDbContext(DbContextOptions<TaskDbContext> options) : DbContext(options)
{
    public DbSet<TaskItem> Tasks => Set<TaskItem>();

    protected override void OnModelCreating(ModelBuilder modelBuilder)
    {
        modelBuilder.Entity<TaskItem>(e =>
        {
            e.HasKey(t => t.Id);
            e.Property(t => t.Title).IsRequired().HasMaxLength(200);
        });
    }
}
