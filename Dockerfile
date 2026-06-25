FROM python:3.11-slim

WORKDIR /app

# Системные зависимости: antiword нужен для парсинга старых .doc (Word 97-2003)
RUN apt-get update \
    && apt-get install -y --no-install-recommends antiword \
    && rm -rf /var/lib/apt/lists/*

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Expose порт
EXPOSE 8000

# Запускаем сервер
CMD ["python", "server.py"]
