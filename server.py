"""
FastAPI сервис для конвертации документов в TXT
"""
from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import tempfile
from pathlib import Path
import os
import shutil
import logging
import json
import base64

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="OpenAI TXT Parser API",
    description="API для конвертации PDF, DOCX в TXT для OpenAI Vector Store",
    version="1.0.0"
)

# CORS для кросс-доменных запросов
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Создаём временную директорию для файлов
TEMP_DIR = Path(tempfile.gettempdir()) / "openai_parser"
TEMP_DIR.mkdir(exist_ok=True)


def build_parser():
    """Ленивая загрузка парсера, чтобы не падать на старте сервиса."""
    try:
        from parser import DocumentParser
        return DocumentParser(output_dir=str(TEMP_DIR))
    except Exception as e:
        logger.exception("Не удалось инициализировать DocumentParser")
        raise HTTPException(status_code=500, detail=f"Parser init error: {str(e)}")


@app.get("/")
def read_root():
    """Главная страница"""
    return {
        "name": "OpenAI TXT Parser API",
        "version": "1.0.0",
        "endpoints": {
            "convert": "POST /convert",
            "convert_and_download": "POST /convert-download",
            "convert_download_json": "POST /convert-download-json",
            "health": "GET /health",
            "docs": "GET /docs"
        }
    }


@app.get("/health")
def health_check():
    """Проверка здоровья сервиса"""
    disk = shutil.disk_usage(TEMP_DIR)
    return {
        "status": "ok",
        "temp_dir": str(TEMP_DIR),
        "disk_free": disk.free
    }


@app.post("/convert")
async def convert_file(file: UploadFile = File(...)):
    """
    Конвертирует загруженный файл в TXT
    
    Returns:
        JSON с путём к сконвертированному файлу и содержимым
    """
    input_path = None
    try:
        # Валидируем расширение файла
        file_ext = Path(file.filename).suffix.lower()
        supported = ['.pdf', '.docx', '.doc', '.txt']
        
        if file_ext not in supported:
            raise HTTPException(
                status_code=400,
                detail=f"Формат {file_ext} не поддерживается. Поддерживаются: {', '.join(supported)}"
            )
        
        # Сохраняем загруженный файл
        input_path = TEMP_DIR / file.filename
        content = await file.read()
        with open(input_path, 'wb') as f:
            f.write(content)
        
        # Парсим файл
        parser = build_parser()
        output_path = parser.convert(str(input_path), output_file=None)
        
        # Читаем результат
        with open(output_path, 'r', encoding='utf-8') as f:
            text_content = f.read()
        
        logger.info(f"✅ Файл {file.filename} успешно конвертирован")
        
        return {
            "status": "success",
            "original_file": file.filename,
            "output_file": Path(output_path).name,
            "size_chars": len(text_content),
            "content": text_content[:1000] + "..." if len(text_content) > 1000 else text_content
        }
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        # Очищаем исходный файл
        if input_path and input_path.exists():
            input_path.unlink()


@app.post("/convert-download")
async def convert_and_download(file: UploadFile = File(...)):
    """
    Конвертирует файл и возвращает готовый TXT для скачивания
    """
    input_path = None
    try:
        file_ext = Path(file.filename).suffix.lower()
        supported = ['.pdf', '.docx', '.doc', '.txt']
        
        if file_ext not in supported:
            raise HTTPException(
                status_code=400,
                detail=f"Формат {file_ext} не поддерживается. Поддерживаются: {', '.join(supported)}"
            )
        
        # Сохраняем загруженный файл
        input_path = TEMP_DIR / file.filename
        content = await file.read()
        with open(input_path, 'wb') as f:
            f.write(content)
        
        # Парсим файл
        parser = build_parser()
        output_path = parser.convert(str(input_path), output_file=None)
        
        logger.info(f"✅ Файл {file.filename} готов к скачиванию")
        
        # Возвращаем файл для скачивания
        return FileResponse(
            output_path,
            media_type='text/plain',
            filename=Path(output_path).name
        )
    
    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))
    
    finally:
        if input_path and input_path.exists():
            input_path.unlink()


@app.post("/convert-download-json")
async def convert_download_json(file: UploadFile = File(...)):
    """
    Конвертирует файл и возвращает:
    - TXT как base64 (для передачи как файл)
    - Полный распарсенный текст
    - Экранированный текст для безопасной вставки в JSON
    """
    input_path = None
    output_path = None
    try:
        file_ext = Path(file.filename).suffix.lower()
        supported = ['.pdf', '.docx', '.doc', '.txt']

        if file_ext not in supported:
            raise HTTPException(
                status_code=400,
                detail=f"Формат {file_ext} не поддерживается. Поддерживаются: {', '.join(supported)}"
            )

        # Сохраняем загруженный файл
        input_path = TEMP_DIR / file.filename
        content = await file.read()
        with open(input_path, 'wb') as f:
            f.write(content)

        # Парсим файл
        parser = build_parser()
        output_path = parser.convert(str(input_path), output_file=None)
        output_name = Path(output_path).name

        # Читаем текст и файл
        with open(output_path, 'r', encoding='utf-8') as f:
            text_content = f.read()

        with open(output_path, 'rb') as f:
            txt_bytes = f.read()

        # Готовим экранированную строку для JSON-полей
        escaped_with_quotes = json.dumps(text_content, ensure_ascii=False)

        logger.info(f"✅ Файл {file.filename} готов в JSON-формате с файлом и текстом")

        return {
            "status": "success",
            "original_file": file.filename,
            "output_file": output_name,
            "mime_type": "text/plain",
            "size_chars": len(text_content),
            "content": text_content,
            "content_json_escaped": escaped_with_quotes,
            "content_json_escaped_raw": escaped_with_quotes[1:-1],
            "file_base64": base64.b64encode(txt_bytes).decode('ascii')
        }

    except Exception as e:
        logger.error(f"❌ Ошибка: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

    finally:
        if input_path and input_path.exists():
            input_path.unlink()
        if output_path and Path(output_path).exists():
            Path(output_path).unlink()


@app.post("/batch")
async def batch_convert(files: list[UploadFile] = File(...)):
    """
    Конвертирует несколько файлов сразу
    
    Returns:
        JSON с результатами для каждого файла
    """
    results = []
    errors = []
    
    try:
        for file in files:
            try:
                file_ext = Path(file.filename).suffix.lower()
                supported = ['.pdf', '.docx', '.doc', '.txt']
                
                if file_ext not in supported:
                    errors.append({
                        "file": file.filename,
                        "error": f"Формат {file_ext} не поддерживается"
                    })
                    continue
                
                # Сохраняем и парсим
                input_path = TEMP_DIR / file.filename
                content = await file.read()
                with open(input_path, 'wb') as f:
                    f.write(content)
                
                parser = build_parser()
                output_path = parser.convert(str(input_path), output_file=None)
                
                with open(output_path, 'r', encoding='utf-8') as f:
                    text_content = f.read()
                
                results.append({
                    "status": "success",
                    "original_file": file.filename,
                    "output_file": Path(output_path).name,
                    "size_chars": len(text_content)
                })
                
                if input_path.exists():
                    input_path.unlink()
            
            except Exception as e:
                errors.append({
                    "file": file.filename,
                    "error": str(e)
                })
        
        logger.info(f"✅ Обработано: {len(results)} файлов, ошибок: {len(errors)}")
        
        return {
            "total": len(files),
            "successful": len(results),
            "failed": len(errors),
            "results": results,
            "errors": errors if errors else None
        }
    
    except Exception as e:
        logger.error(f"❌ Ошибка при пакетной обработке: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=int(os.environ.get("PORT", "8000")))
