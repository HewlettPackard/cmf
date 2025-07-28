-- Migration: Create label_index table for full-text search of CSV label content
-- This migration adds the label_index table to support searching CSV label content
-- through the existing artifact search functionality

-- Create the label_index table
CREATE TABLE IF NOT EXISTS label_index (
    id SERIAL PRIMARY KEY,
    file_name VARCHAR(255) NOT NULL,
    file_path TEXT NOT NULL,
    row_index INTEGER NOT NULL,
    content TEXT NOT NULL,
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
-- This trigger will populate the tsvector column whenever content is inserted or updated
CREATE OR REPLACE FUNCTION update_label_search_vector() RETURNS trigger AS $$
BEGIN
    NEW.search_vector := to_tsvector('english', COALESCE(NEW.content, ''));
    NEW.updated_at := EXTRACT(EPOCH FROM NOW()) * 1000;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Create the trigger
DROP TRIGGER IF EXISTS trigger_update_label_search_vector ON label_index;
CREATE TRIGGER trigger_update_label_search_vector
    BEFORE INSERT OR UPDATE ON label_index
    FOR EACH ROW EXECUTE FUNCTION update_label_search_vector();

-- Create a function to search labels with ranking
CREATE OR REPLACE FUNCTION search_labels(search_query TEXT, result_limit INTEGER DEFAULT 10)
RETURNS TABLE (
    file_name VARCHAR(255),
    row_index INTEGER,
    content TEXT,
    metadata JSONB,
    relevance_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        li.file_name,
        li.row_index,
        li.content,
        li.metadata,
        ts_rank(li.search_vector, plainto_tsquery('english', search_query))::REAL as relevance_score
    FROM label_index li
    WHERE li.search_vector @@ plainto_tsquery('english', search_query)
    ORDER BY relevance_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Create a function to find artifacts with matching labels
CREATE OR REPLACE FUNCTION find_artifacts_with_label_matches(search_query TEXT, result_limit INTEGER DEFAULT 10)
RETURNS TABLE (
    artifact_id INTEGER,
    artifact_name VARCHAR(255),
    artifact_uri TEXT,
    label_file VARCHAR(255),
    matching_content TEXT,
    relevance_score REAL
) AS $$
BEGIN
    RETURN QUERY
    SELECT DISTINCT
        a.id as artifact_id,
        a.name as artifact_name,
        a.uri as artifact_uri,
        li.file_name as label_file,
        li.content as matching_content,
        ts_rank(li.search_vector, plainto_tsquery('english', search_query))::REAL as relevance_score
    FROM artifact a
    JOIN artifactproperty ap ON a.id = ap.artifact_id
    JOIN label_index li ON SPLIT_PART(ap.string_value, ':', 1) = li.file_name
    WHERE ap.name = 'labels_uri'
      AND li.search_vector @@ plainto_tsquery('english', search_query)
    ORDER BY relevance_score DESC
    LIMIT result_limit;
END;
$$ LANGUAGE plpgsql;

-- Add comments for documentation
COMMENT ON TABLE label_index IS 'Stores indexed CSV label content for full-text search integration with artifact search';
COMMENT ON COLUMN label_index.file_name IS 'Name of the CSV label file (without path)';
COMMENT ON COLUMN label_index.file_path IS 'Full path to the CSV label file';
COMMENT ON COLUMN label_index.row_index IS 'Row number within the CSV file (0-based)';
COMMENT ON COLUMN label_index.content IS 'Concatenated content of the CSV row for search';
COMMENT ON COLUMN label_index.metadata IS 'Additional metadata about the label entry (JSON format)';
COMMENT ON COLUMN label_index.search_vector IS 'PostgreSQL tsvector for full-text search';
COMMENT ON COLUMN label_index.created_at IS 'Timestamp when the record was created (milliseconds since epoch)';
COMMENT ON COLUMN label_index.updated_at IS 'Timestamp when the record was last updated (milliseconds since epoch)';

-- Grant permissions (adjust as needed for your setup)
-- GRANT SELECT, INSERT, UPDATE, DELETE ON label_index TO your_app_user;
-- GRANT USAGE, SELECT ON SEQUENCE label_index_id_seq TO your_app_user;

-- Example usage queries (for testing):
-- 
-- 1. Search for labels containing "data":
-- SELECT * FROM search_labels('data', 5);
--
-- 2. Find artifacts with labels containing "training":
-- SELECT * FROM find_artifacts_with_label_matches('training', 10);
--
-- 3. Manual search with custom ranking:
-- SELECT file_name, content, ts_rank(search_vector, plainto_tsquery('english', 'your_search_term')) as rank
-- FROM label_index 
-- WHERE search_vector @@ plainto_tsquery('english', 'your_search_term')
-- ORDER BY rank DESC;
