import json
import os
import pandas as pd
from pathlib import Path
from typing import Dict, List, Any
import base64


class PersistentStorage:
    """
    Система постоянного хранения данных для Graph Builder

    Сохраняет данные на диск, чтобы они были доступны между сессиями браузера.

    Структура хранилища:
    .storage/
        excel_configs/     - Excel конфигурации в JSON
        graphs/            - Графики в SVG + метаданные
            metadata.json  - Информация о всех графиках
    """

    def __init__(self, base_dir: str = ".storage"):
        self.base_dir = Path(base_dir)
        self.excel_dir = self.base_dir / "excel_configs"
        self.graphs_dir = self.base_dir / "graphs"
        self.graphs_metadata_file = self.graphs_dir / "metadata.json"

        # Создаем директории если их нет
        self._init_storage()

    def _init_storage(self):
        """Инициализация структуры хранилища"""
        try:
            self.base_dir.mkdir(exist_ok=True)
            self.excel_dir.mkdir(exist_ok=True)
            self.graphs_dir.mkdir(exist_ok=True)

            # Создаем файл метаданных графиков если его нет
            if not self.graphs_metadata_file.exists():
                self._save_json(self.graphs_metadata_file, [])
        except Exception as e:
            print(f"Warning: Could not initialize storage: {e}")

    def _save_json(self, filepath: Path, data: Any):
        """Сохранить данные в JSON файл"""
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
        except Exception as e:
            print(f"Error saving JSON to {filepath}: {e}")

    def _load_json(self, filepath: Path) -> Any:
        """Загрузить данные из JSON файла"""
        try:
            if filepath.exists():
                with open(filepath, 'r', encoding='utf-8') as f:
                    return json.load(f)
        except Exception as e:
            print(f"Error loading JSON from {filepath}: {e}")
        return None

    # ========== Excel конфигурации ==========

    def save_excel_config(self, name: str, dataframe: pd.DataFrame):
        """Сохранить Excel конфигурацию на диск"""
        try:
            # Преобразуем DataFrame в список словарей
            config_data = dataframe.to_dict(orient='records')

            # Безопасное имя файла
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
            filepath = self.excel_dir / f"{safe_name}.json"

            self._save_json(filepath, config_data)
            return True
        except Exception as e:
            print(f"Error saving Excel config '{name}': {e}")
            return False

    def load_excel_configs(self) -> Dict[str, pd.DataFrame]:
        """Загрузить все Excel конфигурации с диска"""
        configs = {}
        try:
            for filepath in self.excel_dir.glob("*.json"):
                name = filepath.stem
                config_data = self._load_json(filepath)
                if config_data:
                    configs[name] = pd.DataFrame(config_data)
        except Exception as e:
            print(f"Error loading Excel configs: {e}")
        return configs

    def delete_excel_config(self, name: str):
        """Удалить Excel конфигурацию с диска"""
        try:
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
            filepath = self.excel_dir / f"{safe_name}.json"
            if filepath.exists():
                filepath.unlink()
                return True
        except Exception as e:
            print(f"Error deleting Excel config '{name}': {e}")
        return False

    # ========== Графики ==========

    def save_graph(self, name: str, timestamp: str, graph_type: str, svg_data: bytes):
        """Сохранить график на диск"""
        try:
            # Создаем уникальное имя файла
            safe_name = "".join(c for c in name if c.isalnum() or c in (' ', '_', '-')).strip()
            safe_timestamp = timestamp.replace(':', '-')
            filename = f"{safe_name}_{safe_timestamp}.svg"
            filepath = self.graphs_dir / filename

            # Сохраняем SVG файл
            with open(filepath, 'wb') as f:
                f.write(svg_data)

            # Обновляем метаданные
            metadata = self._load_json(self.graphs_metadata_file) or []
            metadata.append({
                'name': name,
                'timestamp': timestamp,
                'type': graph_type,
                'filename': filename
            })
            self._save_json(self.graphs_metadata_file, metadata)

            return True
        except Exception as e:
            print(f"Error saving graph '{name}': {e}")
            return False

    def load_graphs(self) -> List[Dict[str, Any]]:
        """Загрузить все графики с диска"""
        graphs = []
        try:
            metadata = self._load_json(self.graphs_metadata_file) or []

            for entry in metadata:
                filepath = self.graphs_dir / entry['filename']
                if filepath.exists():
                    with open(filepath, 'rb') as f:
                        svg_data = f.read()

                    graphs.append({
                        'name': entry['name'],
                        'timestamp': entry['timestamp'],
                        'type': entry.get('type', 'unknown'),
                        'svg_data': svg_data
                    })
        except Exception as e:
            print(f"Error loading graphs: {e}")
        return graphs

    def delete_graph(self, name: str, timestamp: str):
        """Удалить график с диска"""
        try:
            # Загружаем метаданные
            metadata = self._load_json(self.graphs_metadata_file) or []

            # Находим и удаляем график
            new_metadata = []
            for entry in metadata:
                if entry['name'] == name and entry['timestamp'] == timestamp:
                    # Удаляем SVG файл
                    filepath = self.graphs_dir / entry['filename']
                    if filepath.exists():
                        filepath.unlink()
                else:
                    new_metadata.append(entry)

            # Сохраняем обновленные метаданные
            self._save_json(self.graphs_metadata_file, new_metadata)
            return True
        except Exception as e:
            print(f"Error deleting graph '{name}': {e}")
            return False

    def clear_all_graphs(self):
        """Удалить все графики"""
        try:
            # Удаляем все SVG файлы
            for filepath in self.graphs_dir.glob("*.svg"):
                filepath.unlink()

            # Очищаем метаданные
            self._save_json(self.graphs_metadata_file, [])
            return True
        except Exception as e:
            print(f"Error clearing graphs: {e}")
            return False

    # ========== Экспорт/Импорт всей библиотеки ==========

    def export_library(self) -> dict:
        """Экспортировать всю библиотеку в словарь"""
        library = {
            'excel_configs': {},
            'graphs': [],
            'timestamp': None
        }

        try:
            from datetime import datetime
            library['timestamp'] = datetime.now().isoformat()

            # Excel конфигурации
            excel_configs = self.load_excel_configs()
            for name, df in excel_configs.items():
                library['excel_configs'][name] = df.to_dict(orient='records')

            # Графики (сохраняем SVG как base64)
            graphs = self.load_graphs()
            for graph in graphs:
                library['graphs'].append({
                    'name': graph['name'],
                    'timestamp': graph['timestamp'],
                    'type': graph['type'],
                    'svg_data_base64': base64.b64encode(graph['svg_data']).decode('utf-8')
                })
        except Exception as e:
            print(f"Error exporting library: {e}")

        return library

    def import_library(self, library_data: dict, merge: bool = False):
        """Импортировать библиотеку из словаря"""
        try:
            # Если не merge, очищаем существующие данные
            if not merge:
                self.clear_all_graphs()
                for filepath in self.excel_dir.glob("*.json"):
                    filepath.unlink()

            # Импортируем Excel конфигурации
            for name, records in library_data.get('excel_configs', {}).items():
                df = pd.DataFrame(records)
                self.save_excel_config(name, df)

            # Импортируем графики
            for graph in library_data.get('graphs', []):
                svg_data = base64.b64decode(graph['svg_data_base64'])
                self.save_graph(
                    graph['name'],
                    graph['timestamp'],
                    graph.get('type', 'unknown'),
                    svg_data
                )

            return True
        except Exception as e:
            print(f"Error importing library: {e}")
            return False
