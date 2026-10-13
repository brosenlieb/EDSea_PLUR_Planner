FROM python:3.11-slim

WORKDIR /app

# Install system dependencies needed for PostgreSQL driver and OR-Tools compilation
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy and install dependencies from backend/app/requirements.txt
COPY app/requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy all files from the backend directory into the container
COPY . .

EXPOSE 8000

# Start Uvicorn referencing main.py inside the app module
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]