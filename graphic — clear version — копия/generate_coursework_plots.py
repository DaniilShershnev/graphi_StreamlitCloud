#!/usr/bin/env python3
"""
Мастер-скрипт для генерации всех графиков курсовой работы
"""

import sys
import io
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')

import os
import subprocess
import glob
from pathlib import Path

# Пути
GRAPHIC_DIR = Path("D:/graphic")
CONFIGS_DIR = GRAPHIC_DIR / "configs" / "coursework"
OUTPUT_DIR = GRAPHIC_DIR / "output" / "coursework"
MAIN_SCRIPT = GRAPHIC_DIR / "main.py"

def print_header(text):
    """Красивый заголовок"""
    print("\n" + "="*80)
    print(text.center(80))
    print("="*80 + "\n")


def run_config(config_path):
    """
    Запускает main.py для одного конфигурационного файла

    Parameters:
    -----------
    config_path : Path
        Путь к YAML конфигурационному файлу

    Returns:
    --------
    success : bool
        True если график успешно создан
    """
    config_name = config_path.stem
    print(f"Генерация графика: {config_name}")
    print(f"  Конфиг: {config_path}")

    try:
        # Запускаем main.py с конфигом
        result = subprocess.run(
            ["python", str(MAIN_SCRIPT), "--config", str(config_path)],
            capture_output=True,
            text=True,
            timeout=120,
            cwd=str(GRAPHIC_DIR)
        )

        if result.returncode == 0:
            print(f"  ✓ Успешно создан")
            return True
        else:
            print(f"  ✗ Ошибка при создании")
            print(f"  Stderr: {result.stderr[:200]}")
            return False

    except subprocess.TimeoutExpired:
        print(f"  ✗ Таймаут (>120 сек)")
        return False
    except Exception as e:
        print(f"  ✗ Исключение: {e}")
        return False


def convert_svg_to_pdf():
    """Конвертирует все SVG файлы в PDF"""
    print_header("КОНВЕРТАЦИЯ SVG → PDF")

    svg_files = list(OUTPUT_DIR.glob("*.svg"))

    if not svg_files:
        print("⚠ Нет SVG файлов для конвертации")
        return

    print(f"Найдено SVG файлов: {len(svg_files)}")

    convert_script = GRAPHIC_DIR / "convert_svg_to_pdf.py"

    if not convert_script.exists():
        print(f"⚠ Скрипт конвертации не найден: {convert_script}")
        return

    for svg_file in svg_files:
        print(f"\nКонвертация: {svg_file.name}")
        try:
            result = subprocess.run(
                ["python", str(convert_script), str(svg_file)],
                capture_output=True,
                text=True,
                timeout=60,
                cwd=str(GRAPHIC_DIR)
            )

            if result.returncode == 0:
                pdf_file = svg_file.with_suffix('.pdf')
                if pdf_file.exists():
                    print(f"  ✓ {pdf_file.name}")
                else:
                    print(f"  ✗ PDF не создан")
            else:
                print(f"  ✗ Ошибка конвертации")

        except Exception as e:
            print(f"  ✗ Исключение: {e}")


def create_summary():
    """Создает сводку по созданным графикам"""
    print_header("СВОДКА ПО ГРАФИКАМ")

    svg_files = sorted(OUTPUT_DIR.glob("*.svg"))
    pdf_files = sorted(OUTPUT_DIR.glob("*.pdf"))

    print(f"Создано SVG файлов: {len(svg_files)}")
    print(f"Создано PDF файлов: {len(pdf_files)}")

    # Сохраняем список в текстовый файл
    summary_file = OUTPUT_DIR / "GRAPHS_SUMMARY.txt"

    with open(summary_file, 'w', encoding='utf-8') as f:
        f.write("="*80 + "\n")
        f.write("ГРАФИКИ КУРСОВОЙ РАБОТЫ\n")
        f.write("="*80 + "\n\n")

        f.write("ИЗОКЛИНЫ (Nullclines):\n")
        f.write("-"*80 + "\n")
        for file in sorted(OUTPUT_DIR.glob("nullclines_*.svg")):
            f.write(f"  {file.name}\n")
            pdf = file.with_suffix('.pdf')
            if pdf.exists():
                f.write(f"    → {pdf.name}\n")
        f.write("\n")

        f.write("ФАЗОВЫЕ ПОРТРЕТЫ (Phase Portraits):\n")
        f.write("-"*80 + "\n")
        for file in sorted(OUTPUT_DIR.glob("phase_portrait_*.svg")):
            f.write(f"  {file.name}\n")
            pdf = file.with_suffix('.pdf')
            if pdf.exists():
                f.write(f"    → {pdf.name}\n")
        f.write("\n")

        f.write("="*80 + "\n")
        f.write(f"ВСЕГО: {len(svg_files)} SVG, {len(pdf_files)} PDF\n")
        f.write("="*80 + "\n")

    print(f"\nСводка сохранена: {summary_file}")

    # Выводим на экран
    print("\n" + "-"*80)
    print("NULLCLINES:")
    for file in sorted(OUTPUT_DIR.glob("nullclines_*.svg")):
        print(f"  ✓ {file.name}")

    print("\nPHASE PORTRAITS:")
    for file in sorted(OUTPUT_DIR.glob("phase_portrait_*.svg")):
        print(f"  ✓ {file.name}")


def main():
    """Основная функция"""
    print_header("ГЕНЕРАЦИЯ ГРАФИКОВ КУРСОВОЙ РАБОТЫ")

    # Проверка директорий
    if not CONFIGS_DIR.exists():
        print(f"✗ Директория конфигов не найдена: {CONFIGS_DIR}")
        return

    if not OUTPUT_DIR.exists():
        print(f"Создание выходной директории: {OUTPUT_DIR}")
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    # Находим все конфигурационные файлы
    config_files = sorted(CONFIGS_DIR.glob("*.yaml"))

    if not config_files:
        print(f"✗ Конфигурационные файлы не найдены в {CONFIGS_DIR}")
        return

    print(f"Найдено конфигурационных файлов: {len(config_files)}")
    print(f"Выходная директория: {OUTPUT_DIR}\n")

    # Генерируем графики
    print_header("ГЕНЕРАЦИЯ ГРАФИКОВ")

    success_count = 0
    fail_count = 0

    for i, config_file in enumerate(config_files, 1):
        print(f"\n[{i}/{len(config_files)}] ", end="")

        if run_config(config_file):
            success_count += 1
        else:
            fail_count += 1

    # Результаты генерации
    print("\n" + "-"*80)
    print(f"Успешно: {success_count}")
    print(f"Ошибок: {fail_count}")
    print("-"*80)

    if success_count == 0:
        print("\n✗ Ни один график не был создан")
        return

    # Конвертация в PDF
    try:
        convert_svg_to_pdf()
    except Exception as e:
        print(f"\n⚠ Ошибка при конвертации: {e}")

    # Создание сводки
    create_summary()

    print_header("ГОТОВО!")
    print(f"Графики сохранены в: {OUTPUT_DIR}")
    print(f"Всего создано: {success_count} графиков")


if __name__ == "__main__":
    main()
