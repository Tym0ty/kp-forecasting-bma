from fastapi import APIRouter, UploadFile, Form, HTTPException
from fastapi.responses import JSONResponse, FileResponse
from .tasks import process_csv_task
from .db import validate_and_append_to_db, get_data, append_forecast_results
import os
from datetime import date
from pydantic import BaseModel

# Directory to save uploaded and processed files
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

router = APIRouter()

class ForecastRow(BaseModel):
    TANGGAL: date
    TOTAL_JUMLAH: float

class StoreForecast(BaseModel):
    product_id: str
    results: list[ForecastRow]

@router.post("/internal/store-forecast")
async def store_forecast(payload: StoreForecast):
    """
    Internal endpoint: Celery calls this to persist forecast results.
    """
    try:
        append_forecast_results(payload.product_id, payload.results)
    except Exception as e:
        print(f"error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
    return {"status": "ok"}

@router.post("/upload-train-csv/")
async def upload_train_csv(
    file: UploadFile = UploadFile(...)
):
    """
    Endpoint to upload a train CSV file and start processing it asynchronously.
    """
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())

    # Validate and append data to DuckDB
    try:
        validate_and_append_to_db(file_path)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    return JSONResponse(
        {"message": "File uploaded and processed successfully."},
        status_code=200
    )

# Endpoint to trigger CSV processing
@router.post("/process-csv/")
async def process_csv(
    target_product_id : str
):
    """
    Endpoint to process the uploaded CSV file asynchronously.
    """
    # Start the background task
    df = get_data(target_product_id)
    if df.empty:
        raise HTTPException(status_code=404, detail="No data found for the specified product ID.")
    file_path = os.path.join(UPLOAD_DIR, "train.csv")
    df.to_csv(file_path, index=False)

    task = process_csv_task.delay(file_path, target_product_id)
    if not task:
        raise HTTPException(status_code=500, detail="Task submission failed.")
    
    return JSONResponse(
        {"message": "CSV processing started.", "task_id": task.id},
        status_code=202
    )

# Endpoint to check status task
@router.get("/task-status/{task_id}")
async def get_task_status(task_id: str):
    """
    Endpoint to check the status of a Celery task.
    """
    task = process_csv_task.AsyncResult(task_id)
    if task.state == "PENDING":
        response = {
            "state": task.state,
            "status": "Pending..."
        }
    elif task.state != "FAILURE":
        response = {
            "state": task.state,
            "result": task.result
        }
    else:
        response = {
            "state": task.state,
            "error": str(task.info)  # This will be the exception raised
        }
    
    return JSONResponse(response)

@router.get("/download/{filename}")
def download_file(filename: str):
    """
    Endpoint to download the processed CSV file.
    """
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/csv", filename=filename)
    else:
        return JSONResponse({"error": "File not found"}, status_code=404)
    
