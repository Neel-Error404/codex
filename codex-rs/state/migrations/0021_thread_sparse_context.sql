CREATE TABLE thread_sparse_context (
    thread_id TEXT PRIMARY KEY,
    payload TEXT NOT NULL,
    updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
);
