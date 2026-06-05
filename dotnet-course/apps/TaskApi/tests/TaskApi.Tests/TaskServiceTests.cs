using Microsoft.EntityFrameworkCore;
using Microsoft.Extensions.Logging.Abstractions;
using TaskApi.Data;
using TaskApi.Dtos;
using TaskApi.Services;
using Xunit;

namespace TaskApi.Tests;

public class TaskServiceTests
{
    // Each test gets a fresh in-memory database (fast, isolated).
    private static TaskDbContext NewDb() =>
        new(new DbContextOptionsBuilder<TaskDbContext>()
            .UseInMemoryDatabase(Guid.NewGuid().ToString())
            .Options);

    private static TaskService NewService(TaskDbContext db) =>
        new(db, NullLogger<TaskService>.Instance);

    [Fact]
    public async Task Create_then_Get_returns_the_task()
    {
        var svc = NewService(NewDb());

        var created = await svc.CreateAsync(new CreateTaskDto("write tests"));
        var fetched = await svc.GetAsync(created.Id);

        Assert.NotNull(fetched);
        Assert.Equal("write tests", fetched!.Title);
        Assert.False(fetched.IsDone);
    }

    [Fact]
    public async Task Create_trims_title()
    {
        var svc = NewService(NewDb());
        var created = await svc.CreateAsync(new CreateTaskDto("  spaced  "));
        Assert.Equal("spaced", created.Title);
    }

    [Fact]
    public async Task Create_with_blank_title_throws()
    {
        var svc = NewService(NewDb());
        await Assert.ThrowsAsync<ArgumentException>(
            () => svc.CreateAsync(new CreateTaskDto("   ")));
    }

    [Fact]
    public async Task Complete_marks_done_and_sets_timestamp()
    {
        var svc = NewService(NewDb());
        var created = await svc.CreateAsync(new CreateTaskDto("ship it"));

        var ok = await svc.CompleteAsync(created.Id);

        Assert.True(ok);
        var fetched = await svc.GetAsync(created.Id);
        Assert.True(fetched!.IsDone);
        Assert.NotNull(fetched.CompletedAt);
    }

    [Fact]
    public async Task Complete_missing_task_returns_false()
    {
        var svc = NewService(NewDb());
        Assert.False(await svc.CompleteAsync(999));
    }

    [Fact]
    public async Task Delete_removes_the_task()
    {
        var svc = NewService(NewDb());
        var created = await svc.CreateAsync(new CreateTaskDto("temp"));

        Assert.True(await svc.DeleteAsync(created.Id));
        Assert.Null(await svc.GetAsync(created.Id));
    }
}
