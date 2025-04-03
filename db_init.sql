CREATE TABLE IF NOT EXISTS registred_servers(
	id SERIAL PRIMARY KEY,
	server_name VARCHAR(255) NOT NULL,
	ip_or_host VARCHAR(255) NOT NULL
);

