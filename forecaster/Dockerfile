# Stage 1: Dependency installation
FROM python:3.12-slim AS builder

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH="/app"

# Required packages
RUN apt-get update && apt-get install -y \
    libgomp1 \
    supervisor \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /app

# Copy only dependency files
COPY requirements.txt /app/

RUN pip install -r requirements.txt

# Copy the application code
COPY . /app/

# Copy Supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the FastAPI port
EXPOSE 8000

# Start Supervisor
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]