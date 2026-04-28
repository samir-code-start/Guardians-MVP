# Use the official Python lightweight image
FROM python:3.10-slim

# Prevent python from buffering stdout/stderr
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set working directory
WORKDIR /app

# Install system dependencies (needed for OpenCV)
RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the backend codebase
COPY . .

# Expose port 8080 as expected by Cloud Run
EXPOSE 8080

# Command to run the Uvicorn server
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]
