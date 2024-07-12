CREATE TABLE sessions (
    session_id VARCHAR(255) PRIMARY KEY,
    session_password VARCHAR(255) NOT NULL
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id VARCHAR(255) NOT NULL,
    message TEXT NOT NULL,
    category VARCHAR(50) NOT NULL
);
