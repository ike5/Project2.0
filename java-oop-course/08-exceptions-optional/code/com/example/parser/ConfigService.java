package com.example.parser;

import java.util.Optional;
import java.util.Properties;

public final class ConfigService {
    private final Properties props;
    public ConfigService(Properties props) { this.props = props; }

    public Optional<String> get(String key) {
        return Optional.ofNullable(props.getProperty(key));
    }

    public int requireInt(String key) throws ServiceException {
        String raw = get(key).orElseThrow(() -> new ServiceException("missing key: " + key));
        return IntParser.tryParse(raw).orElseThrow(() ->
                new ServiceException("not an int at " + key + ": " + raw));
    }
}
