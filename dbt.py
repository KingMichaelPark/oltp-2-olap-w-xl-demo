import duckdb
import os

DUCKDB_DATABASE_NAME = "homes_olap.duckdb"
SOURCE_TABLE_NAME = "mortgage_rates"  # The original table with raw rates
DBT_MODEL_TABLE_NAME = (
    "dbt_mortgage_rates_report"  # The new table this script will create/replace
)
DBT_AGGREGATE_VIEW_NAME = (
    "dbt_average_adjusted_rate_view"  # The new view for the average
)


def run_dbt_mock_transformation():
    """
    Connects to DuckDB and runs a SQL transformation to create a new table
    with original and adjusted mortgage rates, mimicking a dbt model.
    """
    if not os.path.exists(DUCKDB_DATABASE_NAME):
        print(f"Error: DuckDB database '{DUCKDB_DATABASE_NAME}' not found.")
        print(
            "Please ensure 'cdc_to_duckdb.py' has been run successfully to create it."
        )
        return

    con = None
    try:
        con = duckdb.connect(database=DUCKDB_DATABASE_NAME, read_only=False)
        print(f"Connected to DuckDB database '{DUCKDB_DATABASE_NAME}'.")

        # Check if the source table exists to provide a more specific error message
        # Note: The CREATE OR REPLACE TABLE would fail anyway, but this gives better context.
        source_table_check_query = f"SELECT 1 FROM sqlite_master WHERE type='table' AND name='{SOURCE_TABLE_NAME}';"
        # DuckDB can query its own catalog using information_schema.tables or duckdb_tables()
        # For simplicity, let's try to query the table directly or check duckdb_tables
        try:
            con.execute(f"SELECT 1 FROM {SOURCE_TABLE_NAME} LIMIT 1;")
        except duckdb.CatalogException:
            # A more robust check:
            tables_in_db = con.execute(
                "SELECT table_name FROM information_schema.tables WHERE table_name = ?",
                [SOURCE_TABLE_NAME.lower()],
            ).fetchall()
            if not tables_in_db:
                print(
                    f"Error: Source table '{SOURCE_TABLE_NAME}' not found in DuckDB database '{DUCKDB_DATABASE_NAME}'."
                )
                print("Please ensure 'cdc_to_duckdb.py' has run and populated it.")
                return

        # SQL to create the new table with the transformation.
        # CREATE OR REPLACE TABLE is idempotent: it creates the table or replaces it if it exists.
        # DuckDB's DAYOFWEEK(date) returns 0 for Sunday and 6 for Saturday.
        sql_transform = f"""
        CREATE OR REPLACE TABLE {DBT_MODEL_TABLE_NAME} AS
        SELECT
            date,
            rate AS original_rate,  -- Renaming for clarity in the new table schema
            CASE
                WHEN DAYOFWEEK(date) IN (0, 6) THEN rate / 2.0  -- 0=Sunday, 6=Saturday
                ELSE rate
            END AS adjusted_rate
        FROM
            {SOURCE_TABLE_NAME};
        """

        print(
            f"Executing SQL transformation to create or replace table '{DBT_MODEL_TABLE_NAME}'..."
        )
        con.execute(sql_transform)
        print(
            f"Successfully created/replaced table '{DBT_MODEL_TABLE_NAME}' with transformed data."
        )

        # SQL to create or replace the view for the average adjusted rate.
        # This runs after the DBT_MODEL_TABLE_NAME has been created/updated.
        sql_create_view = f"""
        CREATE OR REPLACE VIEW {DBT_AGGREGATE_VIEW_NAME} AS
        SELECT
            AVG(adjusted_rate) AS average_adjusted_rate
        FROM
            {DBT_MODEL_TABLE_NAME};
        """
        print(f"Executing SQL to create or replace view '{DBT_AGGREGATE_VIEW_NAME}'...")
        con.execute(sql_create_view)
        print(f"Successfully created/replaced view '{DBT_AGGREGATE_VIEW_NAME}'.")

        # Optional: You can uncomment these lines to verify by fetching and printing a few rows
        # print(f"\nSample data from '{DBT_MODEL_TABLE_NAME}':")
        # result = con.execute(f"SELECT * FROM {DBT_MODEL_TABLE_NAME} ORDER BY date LIMIT 5;").fetchall()
        # for row in result:
        #     print(row)

    except duckdb.Error as e:  # Catch DuckDB specific errors
        print(f"A DuckDB error occurred: {e}")
    except Exception as e:
        print(f"An unexpected error occurred: {e}")
    finally:
        if con:
            con.close()
            print("Disconnected from DuckDB.")


if __name__ == "__main__":
    run_dbt_mock_transformation()
    print("\nDBT mock script execution complete.")
