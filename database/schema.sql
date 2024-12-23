CREATE TABLE IF NOT EXISTS accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT NOT NULL,
    password TEXT NOT NULL,
    gpt_status INTEGER NOT NULL,
    midjourney_status INTEGER NOT NULL,
    custom_platforms TEXT,
    usage_count INTEGER NOT NULL,
    added_time TEXT NOT NULL,
    remark TEXT
);
