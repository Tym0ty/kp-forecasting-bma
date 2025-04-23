import duckdb
import datetime
from typing import List


DUCKDB_FILE = "data/train.duckdb"
DUCKDB_TABLE = "train_data"
OUTPUT_TABLE = "forecast_results"

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
    CREATE SEQUENCE IF NOT EXISTS forecast_result_id_seq START 1;
    CREATE TABLE IF NOT EXISTS {OUTPUT_TABLE} (
        id INTEGER PRIMARY KEY DEFAULT nextval('forecast_result_id_seq'),
        product_id TEXT,
        TANGGAL DATE,
        TOTAL_JUMLAH FLOAT
      )
    """)

conn.execute(f"""
    CREATE SEQUENCE IF NOT EXISTS forecast_history_id_seq START 1;
    CREATE TABLE IF NOT EXISTS forecast_history (
        id INTEGER PRIMARY KEY DEFAULT nextval('forecast_history_id_seq'),
        product_id TEXT,
        START_TANGGAL DATE,
        END_TANGGAL DATE,
        TIMESTAMP TIMESTAMP DEFAULT NOW(),
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
    max_id = conn.execute(f"SELECT MAX(id) FROM {OUTPUT_TABLE}").fetchone()[0]
    if max_id is None:
        max_id = 0
    start_tanggal = min(row.TANGGAL for row in rows)
    end_tanggal = max(row.TANGGAL for row in rows)
    conn.execute(
        f"INSERT INTO forecast_history(product_id, START_TANGGAL, END_TANGGAL) VALUES (?, ?, ?)",
        [product_id, start_tanggal, end_tanggal]
    )
    for r in rows:
        # handle both dicts and Pydantic models
        if hasattr(r, "TANGGAL") and hasattr(r, "TOTAL_JUMLAH"):
            tanggal = r.TANGGAL
            total = r.TOTAL_JUMLAH
        else:
            tanggal = r["TANGGAL"]
            total = r["TOTAL_JUMLAH"]

        conn.execute(
          f"INSERT INTO {OUTPUT_TABLE}(product_id, TANGGAL, TOTAL_JUMLAH) VALUES (?, ?, ?)",
          [product_id, tanggal, total]
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
           START_TANGGAL::TEXT as START_TANGGAL, 
           END_TANGGAL::TEXT as END_TANGGAL, 
           TIMESTAMP::TEXT as TIMESTAMP
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

def get_forecast_by_product_id(start_date: str, end_date:str, product_id: str):
    """
    Fetch forecast data for a specific product ID within a date range.

    Args:
        start_date (str): The start date in 'YYYY-MM-DD' format.
        end_date (str): The end date in 'YYYY-MM-DD' format.
        product_id (str): The product ID to filter by.

    Returns:
        List[dict]: A list of dictionaries containing the forecast data.
    """
    conn = get_connection()
    query = f"""
    SELECT TANGGAL::TEXT as TANGGAL, TOTAL_JUMLAH
    FROM {OUTPUT_TABLE}
    WHERE TANGGAL BETWEEN '{start_date}' AND '{end_date}'
      AND product_id = '{product_id}'
    """
    cursor = conn.execute(query)
    result = cursor.fetchall()
    
    columns = [desc[0] for desc in cursor.description]
    conn.close()
    
    return [dict(zip(columns, row)) for row in result]
