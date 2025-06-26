import duckdb
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# --- Configuration ---
DUCKDB_DATABASE_NAME = "homes_olap.duckdb"
# This table is created by dbt.py and should contain adjusted rates
TABLE_NAME = "dbt_mortgage_rates_report"
# Assuming your table has these columns. Adjust if necessary.
DATE_COLUMN = "date"
ADJUSTED_RATE_COLUMN = "adjusted_rate"
OUTPUT_PNG_FILENAME = "adjusted_rates_over_time.png"
# --- End Configuration ---

def fetch_data_from_duckdb() -> pd.DataFrame:
    """Fetches data from the specified DuckDB table."""
    try:
        con = duckdb.connect(database=DUCKDB_DATABASE_NAME, read_only=True)
        query = f"SELECT \"{DATE_COLUMN}\", \"{ADJUSTED_RATE_COLUMN}\" FROM \"{TABLE_NAME}\" ORDER BY \"{DATE_COLUMN}\";"
        df = con.execute(query).fetchdf()
        con.close()
        
        # Ensure the date column is in datetime format
        if not pd.api.types.is_datetime64_any_dtype(df[DATE_COLUMN]):
            df[DATE_COLUMN] = pd.to_datetime(df[DATE_COLUMN])
        
        # Ensure the rate column is numeric
        df[ADJUSTED_RATE_COLUMN] = pd.to_numeric(df[ADJUSTED_RATE_COLUMN])
        
        return df
    except Exception as e:
        print(f"Error fetching data from DuckDB: {e}")
        # Return an empty DataFrame or re-raise, depending on desired error handling
        return pd.DataFrame(columns=[DATE_COLUMN, ADJUSTED_RATE_COLUMN])

def create_and_save_plot(df: pd.DataFrame):
    """Creates a line plot of adjusted rates over time and saves it to a PNG."""
    if df.empty:
        print("No data available to plot.")
        return

    plt.figure(figsize=(12, 6))
    sns.set_theme(style="whitegrid")
    
    ax = sns.lineplot(x=DATE_COLUMN, y=ADJUSTED_RATE_COLUMN, data=df, marker="o")
    
    plt.title(f'Adjusted Mortgage Rates Over Time from {TABLE_NAME}', fontsize=16)
    plt.xlabel('Date', fontsize=14)
    plt.ylabel('Adjusted Rate (%)', fontsize=14)
    
    # Format date axis for better readability
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%Y-%m-%d'))
    plt.xticks(rotation=45, ha='right')
    
    plt.tight_layout() # Adjust layout to prevent labels from being cut off
    
    try:
        plt.savefig(OUTPUT_PNG_FILENAME)
        print(f"Plot saved as {OUTPUT_PNG_FILENAME}")
    except Exception as e:
        print(f"Error saving plot: {e}")
        
    plt.show() # Display the plot interactively

def main():
    """Main function to fetch data and generate the plot."""
    print("Fetching data for the graph...")
    rates_df = fetch_data_from_duckdb()
    
    if not rates_df.empty:
        print("Generating and saving the plot...")
        create_and_save_plot(rates_df)
    else:
        print(f"Could not generate plot because no data was fetched from {TABLE_NAME}.")

if __name__ == "__main__":
    main()
