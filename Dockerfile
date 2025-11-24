FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt ./
RUN pip install --no-cache-dir -r requirements.txt
COPY . /app
ENV PYTHONUNBUFFERED=1
CMD ["python", "main.py", "run-scheduler", "--db", "data/app.db", "--drop", "data/drop", "--processed", "data/processed", "--failed", "data/failed", "--interval", "1"]
