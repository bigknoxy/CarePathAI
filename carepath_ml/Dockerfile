FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app \
    CAREPATH_HOST=0.0.0.0 \
    CAREPATH_PORT=8000

# Install build dependencies for ML wheels
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libgomp1 \
    && rm -rf /var/lib/apt/lists/*

# Create cache directories for faster builds
RUN mkdir -p /root/.cache/huggingface /root/.cache/torch

# Copy requirements first for better Docker layer caching
COPY carepath_ml/requirements.txt /app/requirements.txt

# Install requirements with PyTorch CPU wheels
RUN pip install --no-cache-dir \
    torch==2.1.0 \
    torchvision==0.16.0 \
    -f https://download.pytorch.org/whl/cpu/

RUN pip install --no-cache-dir -r requirements.txt

# Remove build dependencies to reduce image size
RUN apt-get remove -y build-essential && apt-get autoremove -y && rm -rf /var/lib/apt/lists/*

# Copy application code
COPY carepath_ml/ /app/
COPY carepath_ml/basic_main.py /app/basic_main.py

# Create data directories with correct permissions
RUN mkdir -p /app/data/synthetic /app/data/faiss

# Set correct working directory for data
ENV CAREPATH_DATA_DIR=/app/data

# Set entrypoint to basic main for now
ENTRYPOINT ["python", "/app/basic_main.py"]