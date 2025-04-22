FROM python:3.10-slim-buster

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1
ENV PATH="/root/.local/bin:$PATH"
ENV PYTHONPATH=/app

# Set the working directory
WORKDIR /app

# Install system dependencies and Poetry in a single layer
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    supervisor \
    && curl -sSL https://install.python-poetry.org | python3 - \
    && apt-get clean && rm -rf /var/lib/apt/lists/* /tmp/*

# Copy only necessary files for dependency installation
COPY pyproject.toml poetry.lock /app/

# Install only production dependencies
RUN poetry install --no-root --no-cache

# Copy the rest of the application code
COPY . /app/

# Copy Supervisor configuration
COPY supervisord.conf /etc/supervisor/conf.d/supervisord.conf

# Expose the FastAPI port
EXPOSE 8000

# Start Supervisor
CMD ["supervisord", "-c", "/etc/supervisor/conf.d/supervisord.conf"]