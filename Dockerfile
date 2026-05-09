FROM python:3.11-slim

WORKDIR /app

# Копируем requirements и устанавливаем зависимости
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Копируем весь код
COPY . .

# Expose порт
EXPOSE 8000

# Запускаем сервер
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
