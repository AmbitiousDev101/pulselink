# Build stage
FROM python:3.12-slim AS builder

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Runtime stage
FROM python:3.12-slim

# Install Playwright dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    libnss3 \
    libnspr4 \
    libdbus-1-3 \
    libatk1.0-0 \
    libatk-bridge2.0-0 \
    libcups2 \
    libdrm2 \
    libxkbcommon0 \
    libxcomposite1 \
    libxdamage1 \
    libxfixes3 \
    libxrandr2 \
    libgbm1 \
    libpango-1.0-0 \
    libcairo2 \
    libasound2 \
    libatspi2.0-0 \
    libwayland-client0 \
    fonts-liberation \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r pulselink && useradd -r -g pulselink -m pulselink

WORKDIR /app

COPY --from=builder /install /usr/local
COPY . .

# Install Playwright Chromium as root, then fix permissions
RUN playwright install chromium

RUN chown -R pulselink:pulselink /app

# Create screenshots directory
RUN mkdir -p /app/screenshots && chown pulselink:pulselink /app/screenshots

USER pulselink

CMD ["python", "main.py"]
