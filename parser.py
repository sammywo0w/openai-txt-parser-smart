"""
OpenAI TXT Parser - конвертирует PDF, DOCX и другие форматы в TXT
"""
import os
import sys
from pathlib import Path
from typing import Optional
import click

# Импорты для парсинга
try:
    import PyPDF2
except ImportError:
    PyPDF2 = None

try:
    import docx2txt
except ImportError:
    docx2txt = None


class DocumentParser:
    """Парсер документов в TXT формат"""
    
    def __init__(self, output_dir: Optional[str] = None):
        self.output_dir = Path(output_dir or ".")
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def parse_pdf(self, file_path: str) -> str:
        """Парсит PDF файл"""
        if PyPDF2 is None:
            raise ImportError("PyPDF2 не установлен. Установите: pip install PyPDF2")
        
        text = []
        try:
            with open(file_path, 'rb') as file:
                pdf_reader = PyPDF2.PdfReader(file)
                for page_num in range(len(pdf_reader.pages)):
                    page = pdf_reader.pages[page_num]
                    text.append(page.extract_text())
            return "\n".join(text)
        except Exception as e:
            raise Exception(f"Ошибка при парсинге PDF: {str(e)}")
    
    def parse_docx(self, file_path: str) -> str:
        """Парсит DOCX файл"""
        if docx2txt is None:
            raise ImportError("docx2txt не установлен. Установите: pip install docx2txt")

        try:
            content = docx2txt.process(file_path) or ""
            return content
        except Exception as e:
            raise Exception(f"Ошибка при парсинге DOCX: {str(e)}")
    
    def parse_txt(self, file_path: str) -> str:
        """Читает TXT файл"""
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                return file.read()
        except UnicodeDecodeError:
            # Пробуем другую кодировку
            with open(file_path, 'r', encoding='cp1252') as file:
                return file.read()
        except Exception as e:
            raise Exception(f"Ошибка при чтении TXT: {str(e)}")
    
    def convert(self, file_path: str, output_file: Optional[str] = None) -> str:
        """
        Конвертирует файл в TXT
        
        Args:
            file_path: Путь к исходному файлу
            output_file: Имя выходного файла (опционально)
        
        Returns:
            Путь к созданному TXT файлу
        """
        input_path = Path(file_path)
        
        if not input_path.exists():
            raise FileNotFoundError(f"Файл не найден: {file_path}")
        
        # Определяем расширение файла
        extension = input_path.suffix.lower()
        
        click.echo(f"📄 Парсим файл: {input_path.name}")
        
        # Парсим в зависимости от типа
        if extension == '.pdf':
            content = self.parse_pdf(file_path)
        elif extension == '.docx':
            content = self.parse_docx(file_path)
        elif extension == '.txt':
            content = self.parse_txt(file_path)
        else:
            raise ValueError(f"Неподдерживаемый формат: {extension}")
        
        # Определяем имя выходного файла
        if output_file is None:
            output_file = input_path.stem + ".txt"
        
        output_path = self.output_dir / output_file
        
        # Сохраняем результат
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        click.echo(f"✅ Файл сохранён: {output_path}")
        click.echo(f"📊 Размер: {len(content)} символов")
        
        return str(output_path)
    
    def convert_batch(self, input_dir: str, pattern: Optional[str] = None) -> list:
        """
        Конвертирует множество файлов в директории
        
        Args:
            input_dir: Директория с файлами
            pattern: Паттерн поиска файлов (например, "*.pdf")
        
        Returns:
            Список путей к созданным файлам
        """
        input_path = Path(input_dir)
        if not input_path.is_dir():
            raise NotADirectoryError(f"Это не директория: {input_dir}")
        
        # Поддерживаемые форматы
        supported_formats = ['*.pdf', '*.docx', '*.txt']
        
        files_to_process = []
        if pattern:
            files_to_process = list(input_path.glob(pattern))
        else:
            for fmt in supported_formats:
                files_to_process.extend(input_path.glob(fmt))
        
        if not files_to_process:
            click.echo("⚠️  Файлы не найдены")
            return []
        
        click.echo(f"🔄 Найдено {len(files_to_process)} файлов")
        
        results = []
        errors = []
        
        for file_path in files_to_process:
            try:
                output = self.convert(str(file_path))
                results.append(output)
            except Exception as e:
                click.echo(f"❌ Ошибка с файлом {file_path.name}: {str(e)}", err=True)
                errors.append((str(file_path), str(e)))
        
        if results:
            click.echo(f"\n✨ Успешно обработано: {len(results)} файлов")
        if errors:
            click.echo(f"⚠️  Ошибок: {len(errors)}", err=True)
        
        return results


@click.group()
def cli():
    """OpenAI TXT Parser - конвертирует документы в TXT"""
    pass


@cli.command()
@click.argument('input_file', type=click.Path(exists=True))
@click.option('-o', '--output', help='Имя выходного файла (опционально)')
@click.option('-d', '--output-dir', default='.', help='Выходная директория')
def convert(input_file: str, output: Optional[str], output_dir: str):
    """Конвертирует один файл"""
    try:
        parser = DocumentParser(output_dir=output_dir)
        parser.convert(input_file, output)
    except Exception as e:
        click.echo(f"❌ Ошибка: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
@click.argument('input_dir', type=click.Path(exists=True, file_okay=False))
@click.option('-p', '--pattern', help='Паттерн поиска (например, *.pdf)')
@click.option('-d', '--output-dir', default='.', help='Выходная директория')
def batch(input_dir: str, pattern: Optional[str], output_dir: str):
    """Конвертирует все файлы в директории"""
    try:
        parser = DocumentParser(output_dir=output_dir)
        parser.convert_batch(input_dir, pattern)
    except Exception as e:
        click.echo(f"❌ Ошибка: {str(e)}", err=True)
        sys.exit(1)


@cli.command()
def info():
    """Показывает информацию о поддерживаемых форматах"""
    click.echo("""
📋 Поддерживаемые форматы:
  • PDF (.pdf) - PyPDF2
  • DOCX (.docx) - python-docx
  • TXT (.txt) - встроенный

🚀 Примеры использования:

  # Конвертировать один файл
  python parser.py convert document.pdf

  # Конвертировать один файл с указанием выхода
  python parser.py convert document.pdf -o output.txt

  # Конвертировать все PDF в директории
  python parser.py batch ./documents -p "*.pdf"

  # Конвертировать все поддерживаемые форматы
  python parser.py batch ./documents

  # Использовать парсер в коде
  from parser import DocumentParser
  parser = DocumentParser(output_dir="./output")
  parser.convert("file.pdf", "output.txt")
    """)


if __name__ == '__main__':
    cli()
