FROM python:3.11-slim

WORKDIR /app

# OpenCV needs these system libs even in headless mode
RUN apt-get update && apt-get install -y --no-install-recommends \
    libglib2.0-0 libgl1 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# models/ is gitignored — model_loader.py downloads weights from S3 at startup
RUN mkdir -p models uploads

EXPOSE 8080
ENV PORT=8080

CMD ["gunicorn", "app:app", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "4", "--timeout", "120"]
