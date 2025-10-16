FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y \
    netcat-traditional \
    ca-certificates \
    curl \
    iputils-ping \
    gcc \
    python3-dev \
    build-essential \
    && update-ca-certificates \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY . .

RUN mkdir -p /app/conversations /app/logs

EXPOSE 8000

ENV PYTHONPATH=/app
ENV SSL_CERT_FILE=/etc/ssl/certs/ca-certificates.crt
ENV CURL_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt

CMD ["python3", "run.py"]