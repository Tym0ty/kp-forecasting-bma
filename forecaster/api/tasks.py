from celery import Celery
import os
import time
from kp_forecaster.pipeline import run_bma_pipeline

redis_host = os.getenv('REDIS_HOST', 'localhost')

# Configure Celery
celery = Celery(
    "tasks",
    broker=f'redis://{redis_host}:6379/0',
    backend=f'redis://{redis_host}:6379/0'
)

OUTPUT_TABLE = "forecast_results"

@celery.task
def process_csv_task(filepath: str, target_product_id: str):
    """
    Celery task to process the uploaded CSV file and store the results in the database.
    """
    pipeline_results = run_bma_pipeline(filepath, target_product_id)

    if pipeline_results:
        results_df = pipeline_results['future_forecast']
        conn = get_connection()  # Get a new DuckDB connection

        # Ensure the output table exists
        conn.execute(f"""
        CREATE TABLE IF NOT EXISTS {OUTPUT_TABLE} (
            id INTEGER AUTO_INCREMENT,
            product_id TEXT,
            TANGGAL DATE,
            TOTAL_JUMLAH FLOAT
        )
        """)

        # Insert the results into the database
        for _, row in results_df.iterrows():
            conn.execute(f"""
            INSERT INTO {OUTPUT_TABLE} (product_id, TANGGAL, TOTAL_JUMLAH)
            VALUES ('{target_product_id}', '{row['TANGGAL']}', {row['TOTAL_JUMLAH']})
            """)

        conn.close()  # Close the connection
        return {"status": "success", "message": "Results stored in the database"}
    else:
        return {"status": "failed", "message": "Pipeline failed"}

