-- Runs once, the first time the database volume is created.
-- pgvector is used for embedding storage and similarity search (phase 6+).
CREATE EXTENSION IF NOT EXISTS vector;
