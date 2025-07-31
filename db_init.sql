CREATE TABLE IF NOT EXISTS registered_servers(
	id SERIAL,
	server_name VARCHAR(255) NOT NULL,
	host_info VARCHAR(255) NOT NULL PRIMARY KEY,
	last_sync_time BIGINT DEFAULT NULL
);

-- Label indexing table for full-text search of CSV label content
CREATE TABLE IF NOT EXISTS label_index (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    row_index INTEGER NOT NULL,
    content TEXT NOT NULL,
    -- PostgreSQL automatically uses EXTENDED strategy:
    -- - Allows compression AND out-of-line storage
    -- - Compresses first, then moves to TOAST if still large
    metadata JSONB,
    search_vector TSVECTOR,
    created_at BIGINT NOT NULL,
    updated_at BIGINT NOT NULL,

    -- Unique constraint to prevent duplicate entries
    CONSTRAINT unique_label_file_row UNIQUE (file_name, row_index)
);

-- Create indexes for performance
CREATE INDEX IF NOT EXISTS idx_label_index_file_name ON label_index(file_name);
CREATE INDEX IF NOT EXISTS idx_label_index_created_at ON label_index(created_at);

-- Create GIN index for full-text search (most important for performance)
CREATE INDEX IF NOT EXISTS idx_label_index_search_vector ON label_index USING gin(search_vector);

-- Create a trigger to automatically update the search_vector column
CREATE OR REPLACE FUNCTION update_label_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.content, ''));
    NEW.updated_at := EXTRACT(EPOCH FROM NOW()) * 1000;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger (only if table exists)
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'label_index') THEN
        DROP TRIGGER IF EXISTS trigger_update_label_search_vector ON label_index;
        CREATE TRIGGER trigger_update_label_search_vector
            BEFORE INSERT OR UPDATE ON label_index
            FOR EACH ROW EXECUTE FUNCTION update_label_search_vector();
    END IF;
END $$;

