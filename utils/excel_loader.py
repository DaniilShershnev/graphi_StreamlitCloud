import pandas as pd
import os
from typing import List, Dict, Any


class ExcelConfigLoader:
    """
    Загрузка конфигураций графиков из Excel таблицы

    Поддерживает:
    - Чтение .xlsx и .xls файлов
    - Валидацию структуры таблицы
    - Преобразование строк в словари параметров
    - Обработку пустых значений (NaN)
    """

    def __init__(self, excel_file: str, sheet_name: str = None):
        """
        Инициализация загрузчика

        Параметры:
        - excel_file: путь к Excel файлу (.xlsx или .xls)
        - sheet_name: имя листа (None = первый лист)
        """
        self.excel_file = excel_file
        self.sheet_name = sheet_name
        self.df = None
        self.row_count = 0

    def load_table(self) -> pd.DataFrame:
        """
        Читает таблицу из Excel файла

        Возвращает:
        - DataFrame с данными таблицы

        Исключения:
        - FileNotFoundError: файл не найден
        - ValueError: некорректный формат файла
        """
        # Проверка существования файла
        if not os.path.exists(self.excel_file):
            raise FileNotFoundError(f"Excel файл не найден: {self.excel_file}")

        # Проверка расширения
        ext = os.path.splitext(self.excel_file)[1].lower()
        if ext not in ['.xlsx', '.xls']:
            raise ValueError(f"Неподдерживаемый формат файла: {ext}. Используйте .xlsx или .xls")

        try:
            # Чтение Excel файла
            if self.sheet_name:
                self.df = pd.read_excel(self.excel_file, sheet_name=self.sheet_name)
            else:
                self.df = pd.read_excel(self.excel_file)

            # Удаляем полностью пустые строки
            self.df = self.df.dropna(how='all')

            # Убираем лишние пробелы в названиях колонок (преобразуем в строки сначала)
            self.df.columns = self.df.columns.astype(str).str.strip()

            self.row_count = len(self.df)

            if self.row_count == 0:
                raise ValueError("Таблица пустая (нет строк с данными)")

            return self.df

        except Exception as e:
            if "Worksheet" in str(e) and "does not exist" in str(e):
                raise ValueError(f"Лист '{self.sheet_name}' не найден в файле {self.excel_file}")
            raise ValueError(f"Ошибка чтения Excel файла: {str(e)}")

    def validate_table(self) -> bool:
        """
        Проверяет наличие обязательных колонок в таблице

        Обязательные колонки:
        - output: имя выходного файла

        Возвращает:
        - True если валидация прошла успешно

        Исключения:
        - ValueError: отсутствуют обязательные колонки
        """
        if self.df is None:
            raise ValueError("Таблица не загружена. Вызовите load_table() сначала")

        required_columns = ['output']
        missing_columns = [col for col in required_columns if col not in self.df.columns]

        if missing_columns:
            raise ValueError(f"Отсутствуют обязательные колонки: {', '.join(missing_columns)}")

        return True

    def get_all_rows(self) -> List[Dict[str, Any]]:
        """
        Возвращает все строки таблицы как список словарей

        Особенности обработки:
        - NaN значения заменяются на None
        - Пустые строки пропускаются
        - Добавляется поле __row_number__ для отладки

        Возвращает:
        - Список словарей, каждый словарь = строка таблицы
        """
        if self.df is None:
            raise ValueError("Таблица не загружена. Вызовите load_table() сначала")

        rows = []

        for idx, row in self.df.iterrows():
            # Преобразуем строку в словарь
            row_dict = row.to_dict()

            # Заменяем NaN на None для корректной обработки
            row_dict = {k: (None if pd.isna(v) else v) for k, v in row_dict.items()}

            # Добавляем номер строки для отладки (Excel row = idx + 2, т.к. +1 заголовок, +1 индекс с 0)
            row_dict['__row_number__'] = int(idx) + 2

            # Пропускаем строки без output (обязательное поле)
            if row_dict.get('output') is None or str(row_dict.get('output')).strip() == '':
                continue

            rows.append(row_dict)

        return rows

    def get_rows_grouped_by_output(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Группирует строки по значению колонки 'output'

        Используется для построения нескольких кривых на одном графике
        (строки с одинаковым output объединяются)

        Возвращает:
        - Словарь {output_filename: [список строк с этим output]}
        """
        if self.df is None:
            raise ValueError("Таблица не загружена. Вызовите load_table() сначала")

        rows = self.get_all_rows()
        grouped = {}

        for row in rows:
            output = row['output']
            if output not in grouped:
                grouped[output] = []
            grouped[output].append(row)

        return grouped
