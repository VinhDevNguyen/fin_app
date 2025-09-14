FROM python:3.11-slim

RUN apt-get update && apt-get install -y --no-install-recommends \
        && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY . /app
COPY requirements.txt /app/requirements.txt

RUN pip install --no-cache-dir -r requirements.txt

EXPOSE 8000
CMD ["uvicorn", "infrastructure.response.main:app", "--host", "0.0.0.0", "--port", "8000"]