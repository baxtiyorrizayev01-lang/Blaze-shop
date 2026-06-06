-- Blaze CS2 Marketplace — PostgreSQL Init Script
-- Runs once on first container start

-- Extensions
CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- Fast text search
CREATE EXTENSION IF NOT EXISTS btree_gin; -- GIN indexes

-- Optimize PostgreSQL for marketplace workload
ALTER SYSTEM SET shared_buffers       = '256MB';
ALTER SYSTEM SET effective_cache_size = '768MB';
ALTER SYSTEM SET work_mem             = '16MB';
ALTER SYSTEM SET maintenance_work_mem = '128MB';
ALTER SYSTEM SET random_page_cost     = '1.1';  -- SSD
ALTER SYSTEM SET checkpoint_completion_target = '0.9';
ALTER SYSTEM SET wal_buffers          = '16MB';
ALTER SYSTEM SET max_connections      = '200';

SELECT pg_reload_conf();

-- Full-text search index on skins.name (for fast search)
-- (Created after tables are made by SQLAlchemy)
-- Run this after first migration:
-- CREATE INDEX CONCURRENTLY IF NOT EXISTS ix_skins_name_trgm
--   ON skins USING gin (name gin_trgm_ops);
