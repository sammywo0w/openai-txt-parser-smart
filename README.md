# OpenAI TXT Parser

Парсер для преобразования PDF, DOCX и других форматов в .txt для использования с OpenAI Vector Store.

## Установка

1. Клонируйте или скачайте проект:
```bash
cd Openai-txt-parser
```

2. Установите зависимости:
```bash
pip install -r requirements.txt
```

## Поддерживаемые форматы

- **PDF** (.pdf) - с использованием PyPDF2
- **DOCX** (.docx) - с использованием python-docx (включая таблицы)
- **TXT** (.txt) - встроенная поддержка

## Использование

### Командная строка

#### Конвертировать один файл
```bash
python parser.py convert document.pdf
```

Результат сохранится в `document.txt` в текущей директории.

#### Конвертировать с указанием выхода
```bash
python parser.py convert document.pdf -o custom_name.txt
```

#### Конвертировать в специфическую директорию
```bash
python parser.py convert document.pdf -d ./output
```

#### Конвертировать все файлы в директории
```bash
python parser.py batch ./documents
```

Конвертирует все PDF, DOCX и TXT файлы.

#### Конвертировать файлы по паттерну
```bash
python parser.py batch ./documents -p "*.pdf"
```

#### Использовать в Python коде

```python
from parser import DocumentParser

# Создаём парсер с выходной директорией
parser = DocumentParser(output_dir="./output")

# Конвертируем один файл
parser.convert("document.pdf")

# Или конвертируем с пользовательским именем
parser.convert("document.pdf", "my_output.txt")

# Конвертируем все файлы в директории
parser.convert_batch("./documents")

# Конвертируем все PDF в директории
parser.convert_batch("./documents", pattern="*.pdf")
```

## Примеры для OpenAI Vector Store

После конвертации можете использовать TXT файлы с OpenAI:

```python
from openai import OpenAI
from pathlib import Path

client = OpenAI()

# Читаем сконвертированный TXT файл
with open("document.txt", "r", encoding="utf-8") as f:
    content = f.read()

# Создаём vector store (пример для API v1)
vector_store = client.beta.vector_stores.create(
    name="My Documents"
)

# Загружаете файл
file_response = client.beta.vector_stores.files.upload(
    vector_store_id=vector_store.id,
    file=("document.txt", content, "text/plain")
)
```

## Структура проекта

```
Openai-txt-parser/
├── parser.py          # Основной модуль парсера
├── requirements.txt   # Зависимости
└── README.md         # Этот файл
```

## Ошибки и их решение

### ImportError: PyPDF2/python-docx не установлен
```bash
pip install -r requirements.txt
```

### UnicodeDecodeError при чтении TXT
Парсер автоматически пробует cp1252 кодировку, если UTF-8 не работает.

### Пустой результат при парсинге PDF
Некоторые PDF используют специальную кодировку. Попробуйте:
- Пересохранить PDF в стандартный формат
- Использовать онлайн конвертер в качестве предварительной обработки

## Расширение

Для добавления поддержки новых форматов отредактируйте `parser.py`:

```python
def parse_new_format(self, file_path: str) -> str:
    """Парсит новый формат"""
    # Ваш код здесь
    return extracted_text

# И добавьте в метод convert():
elif extension == '.new':
    content = self.parse_new_format(file_path)
```

## Лицензия

MIT
