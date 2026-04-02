FROM python:3.13-slim

WORKDIR /app

# Install deps
COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

# Copy code
COPY src /app/src

# Make src importable
ENV PYTHONPATH=/app/src

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
