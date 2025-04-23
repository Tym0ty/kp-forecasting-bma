import duckdb
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
    conn.execute(f"""
      CREATE TABLE IF NOT EXISTS {OUTPUT_TABLE} (
        id INTEGER PRIMARY KEY,
        product_id TEXT,
        TANGGAL DATE,
        TOTAL_JUMLAH FLOAT
      )
    """)
    max_id = conn.execute(f"SELECT MAX(id) FROM {OUTPUT_TABLE}").fetchone()[0]
    if max_id is None:
        max_id = 0
    for i, r in enumerate(rows):
        # handle both dicts and Pydantic models
        if hasattr(r, "TANGGAL") and hasattr(r, "TOTAL_JUMLAH"):
            tanggal = r.TANGGAL
            total = r.TOTAL_JUMLAH
        else:
            tanggal = r["TANGGAL"]
            total = r["TOTAL_JUMLAH"]

        conn.execute(
          f"INSERT INTO {OUTPUT_TABLE}(id, product_id, TANGGAL, TOTAL_JUMLAH) VALUES ({max_id+i},?, ?, ?)",
          [product_id, tanggal, total]
        )
    conn.close()