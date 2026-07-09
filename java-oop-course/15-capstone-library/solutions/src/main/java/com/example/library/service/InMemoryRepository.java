package com.example.library.service;

import com.example.library.util.Result;

import java.util.List;
import java.util.Map;
import java.util.Optional;
import java.util.concurrent.ConcurrentHashMap;
import java.util.function.Function;

public final class InMemoryRepository<T, ID> implements Repository<T, ID> {
    private final Map<ID, T> store = new ConcurrentHashMap<>();
    private final Function<T, ID> idExtractor;

    public InMemoryRepository(Function<T, ID> idExtractor) {
        this.idExtractor = idExtractor;
    }

    @Override public Optional<T> findById(ID id) { return Optional.ofNullable(store.get(id)); }
    @Override public List<T> findAll()          { return List.copyOf(store.values()); }
    @Override public Result<T, String> save(T value) {
        store.put(idExtractor.apply(value), value);
        return Result.ok(value);
    }
    @Override public boolean deleteById(ID id)   { return store.remove(id) != null; }
    @Override public int size()                  { return store.size(); }
}
