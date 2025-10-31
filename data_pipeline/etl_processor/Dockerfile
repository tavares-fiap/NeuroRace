FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY process_session.py .

# Não definimos um CMD aqui, pois este script será executado sob demanda