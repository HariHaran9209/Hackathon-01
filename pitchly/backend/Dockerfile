FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install python dependencies
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend application source
COPY . /app/

EXPOSE 8000

# Run migrations and start Daphne ASGI server for HTTP & WebSocket support
CMD ["sh", "-c", "python manage.py migrate && daphne -b 0.0.0.0 -p 8000 pitchly_backend.asgi:application"]
