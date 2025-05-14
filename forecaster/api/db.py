import duckdb
import datetime
from typing import List
import os
import pandas as pd

os.makedirs("data", exist_ok=True)
DUCKDB_FILE = "data/train.duckdb"
DUCKDB_TABLE = "train_data"
OUTPUT_TABLE = "forecast_results"

OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

conn = duckdb.connect(DUCKDB_FILE)

# Ensure the table exists
conn.execute(f"""
CREATE TABLE IF NOT EXISTS {DUCKDB_TABLE} (
    id INTEGER,
    CHANNEL INTEGER,
    LOKASI TEXT,
    TANGGAL DATE,
    KODE_BARANG TEXT,
    KLASIFIKASI_BARANG TEXT,
    WARNA_BARANG TEXT,
    UKURAN_BARANG TEXT,
    BERAT_SATUAN FLOAT,
    JUMLAH INTEGER,
    BERAT_TOTAL FLOAT
)
""")

conn.execute(f"""
    CREATE SEQUENCE IF NOT EXISTS forecast_history_id_seq START 1;
    CREATE TABLE IF NOT EXISTS forecast_history (
        id INTEGER PRIMARY KEY DEFAULT nextval('forecast_history_id_seq'),
        product_id TEXT,
        date_start DATE,
        date_end DATE,
        csv_path TEXT,
        timestamp TIMESTAMP DEFAULT NOW()
    )
""")

def get_connection():
    """
    Create and return a new DuckDB connection.
    """
    return duckdb.connect(DUCKDB_FILE)

def validate_and_append_to_db(file_path: str):
    """
    Validate and append data from the uploaded file to the DuckDB table.
    """
    conn = get_connection()  # Create a new connection
    conn.execute(f"CREATE TEMPORARY TABLE temp_upload AS SELECT * FROM read_csv_auto('{file_path}')")

    min_date, max_date = conn.execute("""
    SELECT MIN(TANGGAL), MAX(TANGGAL) FROM temp_upload
    """).fetchone()

    overlapping_data = conn.execute(f"""
    SELECT *
    FROM {DUCKDB_TABLE}
    WHERE TANGGAL BETWEEN CAST('{min_date}' AS DATE) AND CAST('{max_date}' AS DATE)
    """).fetchall()

    if overlapping_data:
        raise ValueError("Uploaded data contains overlapping dates with existing data.")

    conn.execute(f"INSERT INTO {DUCKDB_TABLE} SELECT * FROM temp_upload")
    conn.close()  # Close the connection

def get_all_data():
    """
    Fetch all data from the DuckDB table.
    """
    conn = get_connection()  # Create a new connection
    query = f"SELECT * FROM {DUCKDB_TABLE} ORDER BY TANGGAL"
    df = conn.execute(query).fetchdf()
    conn.close()  # Close the connection
    return df

def get_data(target_product_id: str):
    """
    Fetch data for the specified product ID from the DuckDB table.
    """
    conn = get_connection()  # Create a new connection
    try:
        kode_barang, klasifikasi_barang, warna_barang, ukuran_barang = target_product_id.split("_")
    except ValueError:
        raise ValueError("Invalid target_product_id format. Expected format: KODE_BARANG_KLASIFIKASI_BARANG_WARNA_BARANG_UKURAN_BARANG")

    query = f"""
    SELECT * FROM {DUCKDB_TABLE}
    WHERE KODE_BARANG = '{kode_barang}'
      AND KLASIFIKASI_BARANG = '{klasifikasi_barang}'
      AND WARNA_BARANG = '{warna_barang}'
      AND UKURAN_BARANG = '{ukuran_barang}'
    """
    df = conn.execute(query).fetchdf()
    conn.close()  # Close the connection
    return df

def append_forecast_results(product_id: str, rows: List[dict]):
    conn = get_connection()

    # Determine the date range
    date_start = min(row.TANGGAL for row in rows)
    date_end = max(row.TANGGAL for row in rows)

    # Save results to a CSV file
    timestamp = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
    csv_filename = f"{product_id}_{date_start}_to_{date_end}_{timestamp}.csv"
    csv_path = os.path.join(OUTPUT_DIR, csv_filename)
    df = pd.DataFrame({
        "TANGGAL": [row.TANGGAL for row in rows],
        "TOTAL_JUMLAH": [row.TOTAL_JUMLAH for row in rows]
    })
    df.to_csv(csv_path, index=False)

    # Insert into forecast_history table
    conn.execute(
        f"""
        INSERT INTO forecast_history (product_id, date_start, date_end, csv_path)
        VALUES (?, ?, ?, ?)
        """,
        [product_id, date_start, date_end, csv_path]
    )
    conn.close()

def get_history_forecast(as_dict: bool = False):
    """
    Fetch the forecast history from the database.

    Args:
        as_dict (bool): If True, return the result as a list of dictionaries. 
                        Otherwise, return as a list of tuples.

    Returns:
        List[dict] or List[tuple]: The forecast history data.
    """
    conn = get_connection()
    query = f"""
    SELECT id, product_id, 
           date_start::TEXT as date_start, 
           date_end::TEXT as date_end, 
           csv_path, 
           timestamp::TEXT as timestamp
    FROM forecast_history
    """
    cursor = conn.execute(query)
    result = cursor.fetchall()
    
    if as_dict:
        columns = [desc[0] for desc in cursor.description]
        conn.close()
        return [dict(zip(columns, row)) for row in result]
    
    conn.close()
    return result

def get_forecast_by_id(forecast_id: int):
    """
    Fetch forecast results by ID.

    Args:
        forecast_id (int): The ID of the forecast to fetch.

    Returns:
        pd.DataFrame: A DataFrame containing the forecast results.
    """
    conn = get_connection()
    query = f"""
    SELECT * FROM {OUTPUT_TABLE}
    WHERE id = {forecast_id}
    """
    df = conn.execute(query).fetchdf()
    conn.close()
    return df

def get_train_data_by_product_id(start_data: str, end_date:str, product_id: str):
    """
    Fetch train data for a specific product ID within a date range.

    Args:
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.
        product_id (str): The product ID to filter by.

    Returns:
        List[dict]: A list of dictionaries containing the train data.
    """
    conn = get_connection()
    kode_barang, klasifikasi_barang, warna_barang, ukuran_barang = product_id.split("_")
    query = f"""
    SELECT TANGGAL::TEXT as TANGGAL, SUM(BERAT_TOTAL) as JUMLAH
    FROM {DUCKDB_TABLE}
    WHERE TANGGAL BETWEEN '{start_data}' AND '{end_date}'
      AND KODE_BARANG = '{kode_barang}'
      AND KLASIFIKASI_BARANG = '{klasifikasi_barang}'
      AND WARNA_BARANG = '{warna_barang}'
      AND UKURAN_BARANG = '{ukuran_barang}'
    GROUP BY TANGGAL
    ORDER BY TANGGAL
    """
    cursor = conn.execute(query)
    result = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    
    return [dict(zip(columns, row)) for row in result]

def get_forecast_history_by_id(forecast_id: int):
    """
    Fetch forecast history by ID.

    Args:
        forecast_id (int): The ID of the forecast to fetch.

    Returns:
        pd.DataFrame: A DataFrame containing the forecast history.
    """
    conn = get_connection()
    query = f"""
    SELECT * FROM forecast_history
    WHERE id = {forecast_id}
    LIMIT 1
    """
    df = conn.execute(query).fetchdf()

    csv_path = df['csv_path'].values[0]
    df_forecast = pd.read_csv(csv_path)

    # Convert the DataFrame to a list of dictionaries
    df_forecast = df_forecast.to_dict(orient='records')

    data = {
        "product_id": df['product_id'].values[0],
        "date_start": pd.to_datetime(df['date_start'].values[0]).strftime("%Y-%m-%d"),
        "date_end": pd.to_datetime(df['date_end'].values[0]).strftime("%Y-%m-%d"),
        "timestamp": pd.to_datetime(df['timestamp'].values[0]).strftime("%Y-%m-%d %H:%M:%S"),
        "forecast": df_forecast
    }

    conn.close()
    return data