CREATE TABLE IF NOT EXISTS registered_servers(
	id SERIAL,
	server_name VARCHAR(255) NOT NULL,
	host_info VARCHAR(255) NOT NULL PRIMARY KEY,
	last_sync_time BIGINT DEFAULT NULL
);

