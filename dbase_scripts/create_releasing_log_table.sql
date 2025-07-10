-- Create releasing_log table
CREATE TABLE IF NOT EXISTS releasing_log (
    id SERIAL PRIMARY KEY,
    doc_owner TEXT NOT NULL,
    doc_type TEXT NOT NULL,
    copy_no INTEGER NOT NULL,
    received_by TEXT NOT NULL,
    released_by TEXT NOT NULL,
    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
); 