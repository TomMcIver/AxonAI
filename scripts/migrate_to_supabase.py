"""
Migration script to copy data from old Neon database to new Supabase database.
Handles foreign key constraints by temporarily disabling them.
"""
import os
import sys

from dotenv import load_dotenv
load_dotenv()

import psycopg2
from psycopg2 import sql

SOURCE_URL = os.environ.get("DATABASE_URL")
DEST_URL = os.environ.get("SUPABASE_DB_URL")

if not SOURCE_URL or not DEST_URL:
    print("ERROR: Both DATABASE_URL and SUPABASE_DB_URL must be set")
    sys.exit(1)

if 'sslmode=' not in SOURCE_URL:
    SOURCE_URL += '?sslmode=require' if '?' not in SOURCE_URL else '&sslmode=require'
if 'sslmode=' not in DEST_URL:
    DEST_URL += '?sslmode=require' if '?' not in DEST_URL else '&sslmode=require'

print("=" * 60)
print("Database Migration: Neon -> Supabase")
print("=" * 60)

print("\n[1/5] Connecting to databases...")
source_conn = psycopg2.connect(SOURCE_URL)
source_cur = source_conn.cursor()
print("  ✓ Connected to source (Neon)")

dest_conn = psycopg2.connect(DEST_URL)
dest_cur = dest_conn.cursor()
print("  ✓ Connected to destination (Supabase)")

# Disable foreign key checks
print("\n[2/5] Disabling foreign key constraints...")
dest_cur.execute("SET session_replication_role = replica;")
dest_conn.commit()
print("  ✓ Constraints disabled")

# Get tables
print("\n[3/5] Getting table list...")
source_cur.execute("""
    SELECT table_name FROM information_schema.tables 
    WHERE table_schema = 'public' AND table_type = 'BASE TABLE'
    ORDER BY table_name
""")
tables = [row[0] for row in source_cur.fetchall()]
print(f"  Found {len(tables)} tables")

# Count rows
table_counts = {}
for table in tables:
    source_cur.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table)))
    table_counts[table] = source_cur.fetchone()[0]

total_rows = sum(table_counts.values())
print(f"  Total rows to migrate: {total_rows}")

# Migrate
print("\n[4/5] Migrating data...")
migrated = 0
migrated_rows = 0

for table in tables:
    count = table_counts[table]
    if count == 0:
        continue
    
    try:
        # Get columns
        source_cur.execute(sql.SQL("""
            SELECT column_name FROM information_schema.columns 
            WHERE table_name = %s AND table_schema = 'public'
            ORDER BY ordinal_position
        """), [table])
        columns = [row[0] for row in source_cur.fetchall()]
        
        # Get data
        source_cur.execute(sql.SQL("SELECT * FROM {}").format(sql.Identifier(table)))
        rows = source_cur.fetchall()
        
        # Clear and insert
        dest_cur.execute(sql.SQL("TRUNCATE {} CASCADE").format(sql.Identifier(table)))
        
        col_list = sql.SQL(', ').join([sql.Identifier(c) for c in columns])
        placeholders = sql.SQL(', ').join([sql.Placeholder()] * len(columns))
        insert_query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
            sql.Identifier(table), col_list, placeholders
        )
        
        for row in rows:
            dest_cur.execute(insert_query, row)
        
        dest_conn.commit()
        print(f"  ✓ {table}: {len(rows)} rows")
        migrated += 1
        migrated_rows += len(rows)
        
    except Exception as e:
        print(f"  ✗ {table}: {e}")
        dest_conn.rollback()

# Re-enable constraints
print("\n[5/5] Re-enabling constraints and updating sequences...")
dest_cur.execute("SET session_replication_role = DEFAULT;")
dest_conn.commit()

# Update sequences
for table in tables:
    try:
        dest_cur.execute(sql.SQL("""
            SELECT setval(pg_get_serial_sequence(%s, 'id'), 
                   COALESCE((SELECT MAX(id) FROM {}) + 1, 1), false)
        """).format(sql.Identifier(table)), [table])
        dest_conn.commit()
    except:
        pass

source_conn.close()
dest_conn.close()

print("\n" + "=" * 60)
print(f"Migration complete!")
print(f"  Tables: {migrated}")
print(f"  Rows: {migrated_rows}")
print("=" * 60)
