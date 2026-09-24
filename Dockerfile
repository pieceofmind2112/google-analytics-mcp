FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir . uvicorn starlette

EXPOSE 8080

CMD ["sh", "-c", "uvicorn app:app --host 0.0.0.0 --port ${PORT:-8080}"]
