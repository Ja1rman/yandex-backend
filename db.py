from sqlalchemy import create_engine

db_url = "postgresql://user:user@localhost:5432/yandex"

migrate_script = """
DROP TABLE IF EXISTS updates;
DROP TABLE IF EXISTS relations;
DROP TABLE IF EXISTS items;
DROP EXTENSION IF EXISTS pgcrypto;
DROP TYPE IF EXISTS item_type;

CREATE EXTENSION pgcrypto;
CREATE TYPE item_type AS ENUM ('offer', 'category');

CREATE TABLE items (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), price BIGINT, name VARCHAR(128) NOT NULL, type item_type NOT NULL, update_date TIMESTAMP);
CREATE TABLE relations (parent_id UUID NOT NULL, FOREIGN KEY (parent_id) REFERENCES items(id), child_id UUID NOT NULL, FOREIGN KEY (child_id) REFERENCES items(id), PRIMARY KEY (parent_id, child_id));
"""
engine = create_engine(db_url)

def migrate():
    engine.execute(migrate_script)
