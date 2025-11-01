FROM python:3.9-slim

WORKDIR /app

# Primeiro, atualizamos o pip para a versão mais recente
RUN pip install --upgrade pip

# Agora, com o pip moderno, instalamos os pacotes
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY processing_logic.py .
COPY worker.py .

CMD ["python", "-u", "worker.py"]