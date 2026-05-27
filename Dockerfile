# # Dockerfile
# FROM python:3.11-slim

# # Set the working directory inside the container
# WORKDIR /app

# # Install system dependencies required for PostgreSQL and building Python packages
# RUN apt-get update && apt-get install -y --no-install-recommends \
#     build-essential \
#     libpq-dev \
#     && rm -rf /var/lib/apt/lists/*

# # Copy requirements first to leverage Docker layer caching
# COPY requirements.txt .

# # Install Python dependencies
# RUN pip install --no-cache-dir -r requirements.txt

# # Copy the entire root project into the container's /app working directory
# # This brings in the 'app/' folder, so the structure inside is /app/app/main.py
# COPY . .

# EXPOSE 8000

# # Run the application (overridden by docker-compose for development --reload)
# # CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]

# # For local development
# # CMD ["fastapi", "dev","--port","8000"]


# # For production
# CMD ["fastapi", "run","--host", "0.0.0.0","--port","8000"]



# Dockerfile
FROM python:3.11-slim

# Set the working directory inside the container
WORKDIR /app

# Install system dependencies required for PostgreSQL and building Python packages
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first to leverage Docker layer caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the entire root project into the container's /app working directory
# This brings in the 'app/' folder, so the structure inside is /app/app/main.py
COPY . .

# Run the application (overridden by docker-compose for development --reload)
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]