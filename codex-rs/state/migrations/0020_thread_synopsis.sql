CREATE TABLE thread_synopsis (
    thread_id TEXT PRIMARY KEY,
    synopsis TEXT NOT NULL,
    updated_at INTEGER NOT NULL DEFAULT (unixepoch()),
    FOREIGN KEY(thread_id) REFERENCES threads(id) ON DELETE CASCADE
);
