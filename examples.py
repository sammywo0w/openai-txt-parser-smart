"""
Примеры подключения к OpenAI TXT Parser API
"""

import requests
from pathlib import Path

# ======== КОНФИГУРАЦИЯ ========
API_URL = "http://localhost:8000"  # Измените на адрес вашего сервера
# API_URL = "http://your-server.com:8000"

# ======== ПРИМЕРЫ ИСПОЛЬЗОВАНИЯ ========

def example_single_convert():
    """Конвертировать один файл"""
    print("📄 Конвертируем один файл...")
    
    with open("document.pdf", "rb") as f:
        files = {"file": f}
        response = requests.post(f"{API_URL}/convert", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Успешно: {result['output_file']}")
        print(f"Размер: {result['size_chars']} символов")
        print(f"Содержимое (первые 500 символов):\n{result['content'][:500]}")
    else:
        print(f"❌ Ошибка: {response.json()['detail']}")


def example_convert_and_download():
    """Конвертировать и скачать файл"""
    print("📥 Конвертируем и скачиваем...")
    
    with open("document.docx", "rb") as f:
        files = {"file": f}
        response = requests.post(f"{API_URL}/convert-download", files=files)
    
    if response.status_code == 200:
        # Сохраняем файл
        output_file = f"downloaded_{Path(response.headers.get('filename', 'output.txt')).name}"
        with open(output_file, "wb") as f:
            f.write(response.content)
        print(f"✅ Файл скачан: {output_file}")
    else:
        print(f"❌ Ошибка: {response.text}")


def example_batch_convert():
    """Конвертировать несколько файлов"""
    print("📚 Конвертируем несколько файлов...")
    
    files_to_convert = ["file1.pdf", "file2.docx", "file3.txt"]
    
    with open("file1.pdf", "rb") as f1, \
         open("file2.docx", "rb") as f2, \
         open("file3.txt", "rb") as f3:
        
        files = [
            ("files", f1),
            ("files", f2),
            ("files", f3)
        ]
        response = requests.post(f"{API_URL}/batch", files=files)
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Успешно: {result['successful']}/{result['total']}")
        for item in result['results']:
            print(f"  - {item['original_file']} → {item['output_file']}")
        if result['errors']:
            print("Ошибки:")
            for err in result['errors']:
                print(f"  - {err['file']}: {err['error']}")
    else:
        print(f"❌ Ошибка: {response.json()['detail']}")


def example_check_health():
    """Проверить статус сервера"""
    print("🏥 Проверяем здоровье сервера...")
    
    response = requests.get(f"{API_URL}/health")
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Сервер работает")
        print(f"Свободно на диске: {result['disk_free'] / (1024**3):.2f} GB")
    else:
        print("❌ Сервер недоступен")


def example_openai_integration():
    """Интеграция с OpenAI Vector Store"""
    print("🤖 Отправляем в OpenAI Vector Store...")
    
    from openai import OpenAI
    
    # 1. Конвертируем документ
    with open("large_document.pdf", "rb") as f:
        files = {"file": f}
        response = requests.post(f"{API_URL}/convert", files=files)
    
    if response.status_code != 200:
        print(f"❌ Ошибка конвертации: {response.json()['detail']}")
        return
    
    result = response.json()
    content = result['content']
    
    # 2. Отправляем в OpenAI
    client = OpenAI(api_key="your-openai-api-key")
    
    # Создаём vector store
    vector_store = client.beta.vector_stores.create(name="My Documents")
    print(f"Vector Store создан: {vector_store.id}")
    
    # Загружаем файл
    txt_file = ("document.txt", content, "text/plain")
    file_response = client.beta.vector_stores.files.upload(
        vector_store_id=vector_store.id,
        file=txt_file
    )
    print(f"✅ Файл загружен: {file_response.id}")


# ======== CURL ПРИМЕРЫ ========
"""
# Конвертировать один файл и получить JSON
curl -X POST "http://localhost:8000/convert" \\
  -F "file=@document.pdf"

# Конвертировать и скачать TXT
curl -X POST "http://localhost:8000/convert-download" \\
  -F "file=@document.pdf" \\
  -o output.txt

# Конвертировать несколько файлов
curl -X POST "http://localhost:8000/batch" \\
  -F "files=@file1.pdf" \\
  -F "files=@file2.docx" \\
  -F "files=@file3.txt"

# Проверить статус
curl "http://localhost:8000/health"

# Получить информацию об API
curl "http://localhost:8000/"
"""

# ======== JAVASCRIPT/FETCH ПРИМЕРЫ ========
"""
// Конвертировать один файл (JavaScript)
const formData = new FormData();
formData.append('file', document.getElementById('fileInput').files[0]);

fetch('http://localhost:8000/convert', {
  method: 'POST',
  body: formData
})
.then(response => response.json())
.then(data => {
  console.log('✅ Успешно:', data);
  console.log('Содержимое:', data.content);
})
.catch(error => console.error('❌ Ошибка:', error));

// Конвертировать и скачать (JavaScript)
const formData = new FormData();
formData.append('file', document.getElementById('fileInput').files[0]);

fetch('http://localhost:8000/convert-download', {
  method: 'POST',
  body: formData
})
.then(response => response.blob())
.then(blob => {
  const url = window.URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = 'document.txt';
  a.click();
})
.catch(error => console.error('❌ Ошибка:', error));
"""

# ======== PYTHON ASYNC ПРИМЕРЫ ========
"""
import aiohttp

async def convert_async():
    async with aiohttp.ClientSession() as session:
        with open('document.pdf', 'rb') as f:
            form = aiohttp.FormData()
            form.add_field('file', f, filename='document.pdf')
            
            async with session.post(f'{API_URL}/convert', data=form) as resp:
                result = await resp.json()
                print(result)

# Использование:
import asyncio
asyncio.run(convert_async())
"""

if __name__ == "__main__":
    print("OpenAI TXT Parser - Примеры использования API\\n")
    print("Убедитесь, что сервер запущен: python server.py\\n")
    
    # Раскомментируйте нужный пример:
    # example_check_health()
    # example_single_convert()
    # example_convert_and_download()
    # example_batch_convert()
    # example_openai_integration()
