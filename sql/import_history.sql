
CREATE TABLE IF NOT EXISTS import_history (
    filename VARCHAR(255) PRIMARY KEY,
    expected_rows BIGINT NOT NULL,
    imported_rows BIGINT NOT NULL,
    duration_seconds DOUBLE PRECISION,
    imported_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    status VARCHAR(20) NOT NULL
);
