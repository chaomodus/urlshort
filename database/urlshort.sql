CREATE TABLE users(id SERIAL PRIMARY KEY NOT NULL,name VARCHAR(16),unique(name));
INSERT INTO users (name) VALUES ('anonymous');
CREATE TABLE urls (id BIGSERIAL PRIMARY KEY NOT NULL,uri VARCHAR(512),owner BIGINT REFERENCES users(id),created TIMESTAMP WITH TIME ZONE,unique(uri));
CREATE TABLE tags (tag VARCHAR(32),url BIGINT REFERENCES urls(id),unique(tag, url));
