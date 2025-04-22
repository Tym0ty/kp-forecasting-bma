from fastapi import FastAPI, UploadFile, Form, File
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from celery import Celery
import pandas as pd
import os
import time
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.datastructures import UploadFile as StarletteUploadFile
from starlette.requests import Request
from starlette.responses import Response

class LimitUploadSizeMiddleware(BaseHTTPMiddleware):
    def __init__(self, app, max_upload_size: int):
        super().__init__(app)
        self.max_upload_size = max_upload_size

    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header
        content_length = request.headers.get("content-length")
        if content_length and int(content_length) > self.max_upload_size:
            return Response(
                "Request body too large", status_code=413  # HTTP 413 Payload Too Large
            )
        return await call_next(request)

# Add the middleware to your FastAPI app
app = FastAPI(
    title="CSV Processing API",
    description="An API to upload CSV files, process them asynchronously, and download the results.",
    version="1.0.0",
)

app.add_middleware(LimitUploadSizeMiddleware, max_upload_size=50 * 1024 * 1024)  # 50 MB
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. Replace with specific origins for better security.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)
redis_host = os.getenv('REDIS_HOST', 'localhost')

# Configure Celery
celery = Celery(
    "tasks",
    broker=f'redis://{redis_host}:6379/0',  # Redis as the message broker
    backend=f'redis://{redis_host}:6379/0'  # Redis as the result backend
)

# Directory to save uploaded and processed files
UPLOAD_DIR = "uploads"
OUTPUT_DIR = "output"
os.makedirs(UPLOAD_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

@celery.task
def process_csv_task(filepath: str, target_product_id: str):
    """
    Celery task to process the uploaded CSV file.
    """
    from kp_forecaster.pipeline import run_bma_pipeline

    pipeline_results = run_bma_pipeline(filepath, target_product_id)

    if pipeline_results:
        results_df = pipeline_results['future_forecast']
        timestamp = time.strftime("%Y%m%d%H%M%S")
        output_file = os.path.join(OUTPUT_DIR, f"{timestamp}_future_forecast.csv")
        results_df.to_csv(output_file, index=False)
        return {"status": "success", "output_file": output_file}
    else:
        return {"status": "failed", "message": "Pipeline failed"}

@app.post(
    "/upload-csv/",
    summary="Upload a CSV file for processing",
    description="Upload a CSV file and specify a target product ID. The file will be processed asynchronously, and you can check the task status later.",
    response_description="Returns a task ID for tracking the processing status.",
)
async def upload_csv(
    file: UploadFile = File(...),  # This tells FastAPI to expect a file from form-data
    target_product_id: str = Form(...)  # This tells FastAPI to get this from form-data too
):
    """
    Endpoint to upload a CSV file and start processing it asynchronously.
    """
    print(f"Received file: {file.filename}")
    print(f"Target Product ID: {target_product_id}")
    file_path = os.path.join(UPLOAD_DIR, file.filename)
    with open(file_path, "wb") as f:
        f.write(await file.read())
    task = process_csv_task.delay(file_path, target_product_id)
    return JSONResponse({"task_id": task.id, "message": "File uploaded and processing started."})

@app.get(
    "/task-status/{task_id}",
    summary="Check the status of a processing task",
    description="Provide a task ID to check the status of the CSV processing task. The response will include the status and the output file if completed.",
    response_description="Returns the task status and output file if completed.",
)
def get_task_status(task_id: str):
    """
    Endpoint to check the status of a CSV processing task.
    """
    task = process_csv_task.AsyncResult(task_id)

    if task.state == "PENDING":
        return {"status": "Pending"}
    elif task.state == "SUCCESS":
        result = task.result
        if result["status"] == "success":
            return {"status": "Completed", "output_file": result["output_file"].replace(OUTPUT_DIR + "/", "")}
        else:
            return {"status": "Failed", "message": result["message"]}
    elif task.state == "FAILURE":
        return {"status": "Failed", "message": str(task.info)}
    else:
        return {"status": task.state}

@app.get(
    "/download/{filename}",
    summary="Download the processed CSV file",
    description="Provide the filename to download the processed CSV file.",
    response_description="Returns the processed CSV file.",
)
def download_file(filename: str):
    """
    Endpoint to download the processed CSV file.
    """
    file_path = os.path.join(OUTPUT_DIR, filename)
    if os.path.exists(file_path):
        return FileResponse(file_path, media_type="text/csv", filename=filename)
    else:
        return JSONResponse({"error": "File not found"}, status_code=404)