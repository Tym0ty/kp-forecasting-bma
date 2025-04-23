from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .middleware import LimitUploadSizeMiddleware
from .endpoints import router

# Initialize FastAPI app
app = FastAPI(
    title="CSV Processing API",
    description="An API to upload CSV files, process them asynchronously, and download the results.",
    version="1.0.0",
)

# Add middleware
app.add_middleware(LimitUploadSizeMiddleware, max_upload_size=50 * 1024 * 1024)  # 50 MB
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows all origins. Replace with specific origins for better security.
    allow_credentials=True,
    allow_methods=["*"],  # Allows all HTTP methods (GET, POST, etc.)
    allow_headers=["*"],  # Allows all headers
)

# Include API routes
app.include_router(router)