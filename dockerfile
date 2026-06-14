FROM python:3.13-slim

WORKDIR /app

RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
COPY sources/ sources/
COPY event_types/ event_types/
COPY data/ data/
COPY config.yaml .

RUN pip install --no-cache-dir -e .

CMD ["framework", "serve-api", "--host", "0.0.0.0", "--port", "8000"]