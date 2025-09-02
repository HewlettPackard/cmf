CREATE TABLE IF NOT EXISTS registered_servers(
	id SERIAL,
	server_name VARCHAR(255) NOT NULL,
	server_url VARCHAR(255) NOT NULL PRIMARY KEY,
	last_sync_time BIGINT DEFAULT NULL
);

