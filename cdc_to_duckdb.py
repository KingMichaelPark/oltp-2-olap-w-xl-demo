import sqlite3
import duckdb
import os

SQLITE_DATABASE_NAME = 'homes.db'
DUCKDB_DATABASE_NAME = 'homes_olap.duckdb' # DuckDB will append .duckdb if not present
MORTGAGE_RATES_TABLE_NAME = 'mortgage_rates'

def read_data_from_sqlite():
    """Reads all data from the mortgage_rates table in SQLite."""
    if not os.path.exists(SQLITE_DATABASE_NAME):
        print(f"Error: SQLite database '{SQLITE_DATABASE_NAME}' not found.")
        return None

    conn = sqlite3.connect(SQLITE_DATABASE_NAME)
    cursor = conn.cursor()
    
    print(f"Reading data from SQLite table '{MORTGAGE_RATES_TABLE_NAME}'...")
    cursor.execute(f"SELECT date, rate FROM {MORTGAGE_RATES_TABLE_NAME}")
    data = cursor.fetchall()
    
    conn.close()
    print(f"Successfully read {len(data)} rows from SQLite.")
    return data

def create_duckdb_table_and_insert_data(data):
    """Creates a table in DuckDB and inserts data, converting date strings to DATE type."""
    if not data:
        print("No data provided to insert into DuckDB.")
        return

    # Connect to DuckDB. It will create the file if it doesn't exist.
    con = duckdb.connect(database=DUCKDB_DATABASE_NAME, read_only=False)
    
    # For CDC simulation, we might want to handle existing data.
    # A simple approach for this script is to clear the table first if it's a full reload.
    # Or, use INSERT OR REPLACE or handle conflicts if primary keys were defined.
    # For now, let's assume we might run this multiple times and want to avoid duplicates
    # if we were to add a unique constraint on 'date' in DuckDB.
    # A simple way for this demo is to insert and let DuckDB handle it,
    # or for a true CDC, you'd track changes.
    # For this script, we'll just insert. If you run it multiple times, you'll get duplicate rows
    # unless you add a primary key or unique constraint to the DuckDB table and handle conflicts.
    # Let's make it idempotent by trying to use a temporary staging table for an UPSERT like pattern.

    # Create a temporary staging table
    TEMP_STAGING_TABLE = "staging_mortgage_rates"
    con.execute(f"""
        CREATE TEMP TABLE {TEMP_STAGING_TABLE} (
            date_str TEXT,  -- Keep as TEXT initially for robust loading
            rate DOUBLE
        )
    """)

    # Insert data into the staging table
    # DuckDB's executemany is efficient.
    con.executemany(f"INSERT INTO {TEMP_STAGING_TABLE} (date_str, rate) VALUES (?, ?)", data)
    print(f"Inserted {len(data)} rows into temporary staging table.")

    # Upsert from staging to target table
    # This will insert new rows or update existing ones if a date matches.
    # For this to be a true upsert, mortgage_rates needs a primary key or unique constraint on date.
    # Let's add a UNIQUE constraint to the main table definition.
    con.execute(f"""
        CREATE TABLE IF NOT EXISTS {MORTGAGE_RATES_TABLE_NAME} (
            date DATE UNIQUE,
            rate DOUBLE
        )
    """)

    con.execute(f"""
        INSERT INTO {MORTGAGE_RATES_TABLE_NAME} (date, rate)
        SELECT CAST(date_str AS DATE), rate FROM {TEMP_STAGING_TABLE}
        ON CONFLICT (date) DO UPDATE SET rate = excluded.rate;
    """)
    
    print(f"Data upserted into '{MORTGAGE_RATES_TABLE_NAME}'.")

    # Clean up staging table
    con.execute(f"DROP TABLE {TEMP_STAGING_TABLE}")

    con.close()
    print(f"Data successfully loaded into DuckDB table '{MORTGAGE_RATES_TABLE_NAME}'.")

if __name__ == '__main__':
    # First, ensure the SQLite database and table exist and are populated
    # by running load_rates.py if it hasn't been run yet.
    # For this script, we assume load_rates.py has been run.
    
    sqlite_data = read_data_from_sqlite()
    if sqlite_data:
        create_duckdb_table_and_insert_data(sqlite_data)
        print("CDC simulation process to DuckDB complete.")
    else:
        print("CDC simulation process to DuckDB aborted due to missing SQLite data.")
