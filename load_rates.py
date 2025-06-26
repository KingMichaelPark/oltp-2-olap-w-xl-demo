import sqlite3
import csv
import os

DATABASE_NAME = 'homes.db'
CSV_FILE_NAME = 'june_2025_rates.csv'

def create_database_and_table():
    """Creates the SQLite database and the mortgage_rates table if they don't exist."""
    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS mortgage_rates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT UNIQUE NOT NULL,
            rate REAL NOT NULL
        )
    ''')
    conn.commit()
    conn.close()
    print(f"Database '{DATABASE_NAME}' and table 'mortgage_rates' ensured to exist.")

def load_data_from_csv():
    """Loads mortgage rate data from the CSV file into the mortgage_rates table."""
    if not os.path.exists(CSV_FILE_NAME):
        print(f"Error: CSV file '{CSV_FILE_NAME}' not found.")
        return

    conn = sqlite3.connect(DATABASE_NAME)
    cursor = conn.cursor()

    with open(CSV_FILE_NAME, 'r', newline='') as csvfile:
        csv_reader = csv.DictReader(csvfile)
        rates_to_insert = []
        for row in csv_reader:
            try:
                # Validate data if necessary, e.g., date format, rate is a float
                rates_to_insert.append((row['date'], float(row['rate'])))
            except ValueError:
                print(f"Skipping row with invalid rate: {row}")
                continue
            except KeyError:
                print(f"Skipping row with missing 'date' or 'rate' field: {row}")
                continue
        
        if rates_to_insert:
            try:
                cursor.executemany('''
                    INSERT INTO mortgage_rates (date, rate) VALUES (?, ?)
                    ON CONFLICT(date) DO NOTHING
                ''', rates_to_insert)
                conn.commit()
                print(f"Successfully inserted/updated {len(rates_to_insert)} records from '{CSV_FILE_NAME}'.")
            except sqlite3.IntegrityError as e:
                print(f"An integrity error occurred: {e}") # Should be caught by ON CONFLICT
            except Exception as e:
                print(f"An error occurred during database insertion: {e}")
        else:
            print("No valid data found in CSV to insert.")

    conn.close()

if __name__ == '__main__':
    create_database_and_table()
    load_data_from_csv()
    print("Initial data load process complete.")
