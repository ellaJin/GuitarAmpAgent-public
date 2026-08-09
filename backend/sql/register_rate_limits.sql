CREATE TABLE register_rate_limits (
    ip            text PRIMARY KEY,
    window_start  timestamptz NOT NULL DEFAULT now(),
    request_count int NOT NULL DEFAULT 0
);
