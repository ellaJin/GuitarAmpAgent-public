CREATE TABLE pending_registrations (
    email         text PRIMARY KEY,
    display_name  text,
    password_hash text NOT NULL,
    code_hash     text NOT NULL,
    expires_at    timestamptz NOT NULL,
    attempts      int NOT NULL DEFAULT 0,
    created_at    timestamptz NOT NULL DEFAULT now()
);
