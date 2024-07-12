CREATE TABLE sessions (
    id SERIAL PRIMARY KEY,
    session_name VARCHAR(255) NOT NULL,
    session_password VARCHAR(255) NOT NULL
);

CREATE TABLE messages (
    id SERIAL PRIMARY KEY,
    session_id INTEGER REFERENCES sessions(id),
    message TEXT NOT NULL,
    category VARCHAR(50) NOT NULL
);
