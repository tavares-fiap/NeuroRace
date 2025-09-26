FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir "pandas"
RUN pip install --no-cache-dir "python-socketio[client]"

CMD ["python", "analysis_service.py"]