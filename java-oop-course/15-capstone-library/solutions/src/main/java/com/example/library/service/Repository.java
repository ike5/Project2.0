package com.example.library.service;

import com.example.library.util.Result;

import java.util.List;
import java.util.Optional;
import java.util.function.Function;

public interface Repository<T, ID> {
    Optional<T> findById(ID id);
    List<T> findAll();
    Result<T, String> save(T value);
    boolean deleteById(ID id);
    int size();
}
