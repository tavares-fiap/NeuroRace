FROM python:3.11-slim

WORKDIR /app
COPY . /app

RUN pip install --no-cache-dir "python-socketio"
RUN pip install --no-cache-dir "python-socketio[client]"

CMD ["python", "collector_service.py"]