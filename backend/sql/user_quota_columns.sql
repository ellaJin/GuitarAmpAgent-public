ALTER TABLE users
    ADD COLUMN daily_query_limit int  NOT NULL DEFAULT 10,
    ADD COLUMN daily_token_limit int  NOT NULL DEFAULT 50000,
    ADD COLUMN quota_date        date NOT NULL DEFAULT current_date,
    ADD COLUMN query_count       int  NOT NULL DEFAULT 0,
    ADD COLUMN token_count       int  NOT NULL DEFAULT 0;
