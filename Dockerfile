FROM python:3.12-slim

WORKDIR /app

RUN apt-get update \
    && apt-get install -y --no-install-recommends libpcap0.8 \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .

RUN pip install --no-cache-dir -r requirements.txt

COPY app ./app
COPY pytest.ini .
COPY tests ./tests

RUN mkdir -p /app/data

ENTRYPOINT ["python", "-m", "app.sniffer"]
