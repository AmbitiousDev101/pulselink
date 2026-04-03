# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

RUN groupadd -r pulselink && useradd -r -g pulselink pulselink

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

RUN chown -R pulselink:pulselink /app

USER pulselink

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "1"]
