FROM python:3.11-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Create logs directory
RUN mkdir -p /app/logs

# Copy application code
COPY . .

# Run both the sync service and API
CMD ["sh", "-c", "python sync_service.py & python api.py"]
