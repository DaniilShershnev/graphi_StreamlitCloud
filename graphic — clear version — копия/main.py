import sys
import os
import argparse  #библиотека для парсинга командной строки

# КРИТИЧНО для Windows multiprocessing: устанавливаем non-GUI backend для matplotlib
# ДО любых импортов, которые могут использовать matplotlib
import matplotlib
matplotlib.use('Agg', force=True)

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from utils.config_loader import load_config
from utils.validators import validate_config, merge_params
from utils.excel_loader import ExcelConfigLoader
from utils.config_merger import ConfigMerger
from core.function_plotter import FunctionPlotter
from core.ode_plotter import ODEPlotter
from models.ode_system import ODESystem
import params_global

#Функция ниже определяет типа графика и проверяет корректность типа графика, после чего вызывает либо соответствующий обработчик графика либо выкидывает ошибку Unkown type.
def plot_from_config(config):
    validate_config(config) # проверяет корректность входных данных config, в случае ошибки выбрасывает через raise ошибку и останавливает программу.

    plot_type = config['type']  # извлекаем из словаря config тип графика

    if plot_type == 'function':
        plot_function(config)
    elif plot_type == 'ode_time':
        plot_ode_time(config)
    elif plot_type == 'phase_portrait':
        plot_phase_portrait(config)
    elif plot_type == 'from_excel':
        plot_from_excel(config)
    else:
        raise ValueError(f"Unknown type: {plot_type}")


def write_equilibria_log(equilibria_results, filename='asimptota.txt'):
    """
    Записывает информацию о равновесиях (асимптотах) в текстовый файл.

    Параметры:
    - equilibria_results: список словарей с информацией о равновесиях (каждая кривая - отдельная запись)
    - filename: имя выходного файла

    Формат записи:
    - Группирует равновесия по графикам (по полю 'output')
    - Для ode_time: выводит s*, w*, метод, сходимость
    - Для phase_portrait: дополнительно тип равновесия, устойчивость, собственные значения
    """
    from datetime import datetime
    from collections import defaultdict

    try:
        # Группируем равновесия по графикам
        graphs_dict = defaultdict(list)
        for result in equilibria_results:
            output_file = result.get('output', 'N/A')
            graphs_dict[output_file].append(result)

        with open(filename, 'w', encoding='utf-8') as f:
            # Заголовок
            f.write("=" * 60 + "\n")
            f.write("АНАЛИЗ РАВНОВЕСИЙ (АСИМПТОТ)\n")
            f.write(f"Дата и время: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"Всего графиков: {len(graphs_dict)}\n")
            f.write(f"Всего кривых с равновесиями: {len(equilibria_results)}\n")
            f.write("=" * 60 + "\n\n")

            # Информация по каждому графику
            for graph_idx, (output_file, equilibria_list) in enumerate(sorted(graphs_dict.items()), 1):
                f.write(f"[{graph_idx}] График: {output_file}\n")

                # Тип графика (берем из первого равновесия)
                graph_type = equilibria_list[0].get('type', 'N/A')
                f.write(f"    Тип: {graph_type}\n")
                f.write(f"    Количество кривых: {len(equilibria_list)}\n\n")

                # Выводим информацию по каждой кривой
                for curve_idx, result in enumerate(equilibria_list, 1):
                    s_star = result.get('s_star')
                    w_star = result.get('w_star')
                    converged = result.get('converged', False)
                    method = result.get('method', 'N/A')

                    if len(equilibria_list) > 1:
                        f.write(f"    --- Кривая {curve_idx} ---\n")

                    # Выводим значения равновесий
                    if s_star is not None:
                        f.write(f"    s* = {s_star:.6f}\n")
                    if w_star is not None:
                        f.write(f"    w* = {w_star:.6f}\n")

                    # Сходимость
                    f.write(f"    Сходимость: {'Да' if converged else 'Нет'}\n")

                    if converged:
                        f.write(f"    Метод: {method}\n")

                        # Для фазовых портретов - дополнительная информация
                        if graph_type == 'phase_portrait':
                            stability = result.get('stability')
                            eq_type = result.get('equilibrium_type')
                            eigenvalues = result.get('eigenvalues')

                            if stability:
                                f.write(f"    Устойчивость: {stability}\n")
                            if eq_type:
                                f.write(f"    Тип равновесия: {eq_type}\n")
                            if eigenvalues:
                                # Форматируем собственные значения
                                ev_strs = []
                                for ev in eigenvalues:
                                    if isinstance(ev, complex):
                                        if abs(ev.imag) < 1e-10:
                                            ev_strs.append(f"{ev.real:.4f}")
                                        else:
                                            sign = "+" if ev.imag >= 0 else "-"
                                            ev_strs.append(f"{ev.real:.4f} {sign} {abs(ev.imag):.4f}i")
                                    else:
                                        ev_strs.append(f"{ev:.4f}")
                                f.write(f"    Собственные значения: {', '.join(ev_strs)}\n")
                    else:
                        f.write(f"    Примечание: Равновесие не найдено или не сошлось\n")

                    if len(equilibria_list) > 1 and curve_idx < len(equilibria_list):
                        f.write("\n")

                f.write("\n")

            # Футер
            f.write("=" * 60 + "\n")

    except Exception as e:
        print(f"Ошибка записи файла равновесий: {e}")


def _build_single_graph(args):
    """
    Вспомогательная функция для построения одного графика в отдельном процессе.
    Используется для параллелизации.

    Параметры:
    - args: кортеж (output_file, rows, base_config, graph_type, params_global_dict)

    Возвращает:
    - dict: {'success': bool, 'output': str, 'error': str (если success=False)}
    """
    output_file, rows, base_config, graph_type, params_global_dict = args

    try:
        # КРИТИЧНО для Windows: принудительно устанавливаем non-GUI backend
        # ДО любых импортов, которые могут использовать matplotlib
        import matplotlib
        matplotlib.use('Agg', force=True)

        # ВАЖНО: В дочернем процессе нужно восстановить params_global
        # Создаем временный объект с атрибутами из словаря
        import sys
        import os
        sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

        # Импортируем params_global и устанавливаем значения
        import params_global
        for key, value in params_global_dict.items():
            setattr(params_global, key, value)

        # Создаем конфигурацию для этого графика
        graph_config = _create_graph_config_from_rows(rows, base_config, graph_type)

        # Определяем тип графика
        actual_type = graph_config.get('type', graph_type)

        # Добавляем флаг тихого режима для дочерних процессов
        # (чтобы избежать путаницы в консоли от print в разных процессах)
        graph_config['_silent'] = True

        # Строим график и собираем информацию о равновесиях
        equilibria_info = None
        if actual_type == 'ode_time':
            equilibria_info = plot_ode_time(graph_config)
        elif actual_type == 'phase_portrait':
            equilibria_info = plot_phase_portrait(graph_config)
        elif actual_type == 'function':
            plot_function(graph_config)
        else:
            raise ValueError(f"Неизвестный graph_type: {actual_type}")

        # ВАЖНО: закрываем все фигуры matplotlib для освобождения памяти
        import matplotlib.pyplot as plt
        plt.close('all')

        # Возвращаем успех, имя файла, количество кривых, и информацию о равновесиях
        return (True, output_file, len(rows), equilibria_info)

    except Exception as e:
        import traceback
        import matplotlib.pyplot as plt
        plt.close('all')

        # Возвращаем кортеж: (success, output, error_msg, None) с полным traceback
        error_msg = f"{type(e).__name__}: {str(e)}\n{traceback.format_exc()}"
        return (False, output_file, error_msg, None)


def plot_from_excel(config):
    """
    Обрабатывает type: from_excel - построение графиков из Excel таблицы

    Алгоритм:
    1. Загружает Excel таблицу
    2. Группирует строки по значению 'output' (для построения нескольких кривых на одном графике)
    3. Для каждой группы строк:
       - Объединяет base_config с параметрами из Excel
       - Создает конфигурацию графика
       - Вызывает соответствующую функцию построения
    4. Выводит отчет о построенных графиках
    """
    print(f"\n{'='*60}")
    print(f"Построение графиков из Excel таблицы")
    print(f"{'='*60}\n")

    # Извлекаем параметры из конфига
    excel_file = config.get('excel_file')
    sheet_name = config.get('sheet_name')
    base_config = config.get('base_config', {})
    graph_type = base_config.get('graph_type', 'ode_time')

    if not excel_file:
        raise ValueError("Параметр 'excel_file' обязателен для type: from_excel")
    if not base_config:
        raise ValueError("Параметр 'base_config' обязателен для type: from_excel")

    # Загружаем Excel таблицу
    print(f"Загрузка Excel: {excel_file}")
    if sheet_name:
        print(f"Лист: {sheet_name}")

    try:
        loader = ExcelConfigLoader(excel_file, sheet_name)
        loader.load_table()
        loader.validate_table()
    except Exception as e:
        print(f"\n❌ Ошибка загрузки Excel: {str(e)}")
        raise

    # Группируем строки по output (для объединения кривых на одном графике)
    grouped_rows = loader.get_rows_grouped_by_output()
    total_graphs = len(grouped_rows)
    print(f"Найдено уникальных графиков (по output): {total_graphs}")
    print(f"Всего строк в таблице: {loader.row_count}\n")

    # Счетчики для отчета
    success_count = 0
    error_count = 0
    errors_list = []
    equilibria_results = []  # Список для сбора информации о равновесиях

    # Проверяем, нужна ли параллелизация
    parallel = config.get('parallel', False)
    num_workers = config.get('num_workers', 8)

    if parallel:
        # ===== ПАРАЛЛЕЛЬНЫЙ РЕЖИМ =====
        print(f"Режим: ПАРАЛЛЕЛЬНЫЙ (воркеров: {num_workers})\n")

        from multiprocessing import Pool

        # Подготавливаем данные для передачи в дочерние процессы
        # Преобразуем params_global в словарь
        params_global_dict = vars(params_global)

        # Создаем список задач
        tasks = [
            (output_file, rows, base_config, graph_type, params_global_dict)
            for output_file, rows in grouped_rows.items()
        ]

        print(f"Построение {len(tasks)} графиков...\n")

        # Запускаем параллельное построение с timeout
        with Pool(num_workers) as pool:
            # Запускаем все задачи асинхронно
            async_results = [(task[0], pool.apply_async(_build_single_graph, (task,))) for task in tasks]

            # Собираем результаты с timeout
            for idx, (output_file, async_result) in enumerate(async_results, 1):
                try:
                    # Ждём результат максимум 120 секунд (для жёстких систем)
                    result = async_result.get(timeout=120)
                    success = result[0]
                    data = result[2]
                    equilibria_info = result[3] if len(result) > 3 else None

                    if success:
                        success_count += 1
                        # Сохраняем информацию о равновесиях
                        if equilibria_info:
                            # Теперь equilibria_info - список равновесий для графика
                            if isinstance(equilibria_info, list):
                                equilibria_results.extend(equilibria_info)
                            else:
                                equilibria_results.append(equilibria_info)
                    else:
                        error_msg = data
                        error_count += 1
                        errors_list.append({
                            'output': output_file,
                            'error': error_msg,
                            'rows': ['?']
                        })

                except Exception as e:
                    # Timeout или другая ошибка
                    error_count += 1
                    errors_list.append({
                        'output': output_file,
                        'error': f"Timeout или ошибка: {str(e)}",
                        'rows': ['?']
                    })
                    print(f"Шаг: {idx}/{len(tasks)} [TIMEOUT/ERROR]")
                    continue

                print(f"Шаг: {idx}/{len(tasks)}")

    else:
        # ===== ПОСЛЕДОВАТЕЛЬНЫЙ РЕЖИМ (по умолчанию) =====
        # Обрабатываем каждую группу строк (каждый выходной файл)
        for idx, (output_file, rows) in enumerate(grouped_rows.items(), 1):
            print(f"[{idx}/{total_graphs}] {output_file} ({len(rows)} кривых) ... ", end='')

            try:
                # Создаем конфигурацию для этого графика
                graph_config = _create_graph_config_from_rows(rows, base_config, graph_type)

                # Вызываем соответствующую функцию построения
                # ВАЖНО: используем graph_config['type'], т.к. он может быть переопределен из Excel
                actual_type = graph_config.get('type', graph_type)

                equilibria_info = None
                if actual_type == 'ode_time':
                    equilibria_info = plot_ode_time(graph_config)
                elif actual_type == 'phase_portrait':
                    equilibria_info = plot_phase_portrait(graph_config)
                elif actual_type == 'function':
                    plot_function(graph_config)
                else:
                    raise ValueError(f"Неизвестный graph_type: {actual_type}")

                # Сохраняем информацию о равновесиях
                if equilibria_info:
                    # Теперь equilibria_info - список равновесий для графика
                    if isinstance(equilibria_info, list):
                        equilibria_results.extend(equilibria_info)
                    else:
                        equilibria_results.append(equilibria_info)

                print("[OK] создан")
                success_count += 1

            except Exception as e:
                print(f"[ERROR] ошибка")
                error_count += 1
                import traceback
                error_details = f"{type(e).__name__}: {str(e)}"
                # Для отладки можно раскомментировать:
                # error_details += "\n" + traceback.format_exc()
                # print(f"  Детали: {error_details}")
                errors_list.append({
                    'output': output_file,
                    'error': error_details,
                    'rows': [row.get('__row_number__', '?') for row in rows]
                })

    # Выводим итоговый отчет
    print(f"\n{'='*60}")
    print(f"РЕЗУЛЬТАТ:")
    print(f"  Успешно построено: {success_count}")
    print(f"  Ошибок: {error_count}")
    print(f"{'='*60}\n")

    # Если были ошибки, выводим детали
    if errors_list:
        print("ДЕТАЛИ ОШИБОК:")
        for err in errors_list:
            print(f"  • {err['output']} (строки Excel: {err['rows']})")
            print(f"    Ошибка: {err['error']}\n")

    # Записываем информацию о равновесиях в файл
    if equilibria_results:
        write_equilibria_log(equilibria_results, 'asimptota.txt')
        print(f"Информация о равновесиях сохранена в asimptota.txt ({len(equilibria_results)} графиков)\n")


def _create_graph_config_from_rows(rows, base_config, graph_type):
    """
    Создает конфигурацию графика из одной или нескольких строк Excel

    Параметры:
    - rows: список строк Excel (словари) с одинаковым output
    - base_config: базовая конфигурация из YAML
    - graph_type: тип графика (ode_time, phase_portrait, function) из base_config

    Возвращает:
    - Конфигурация для построения графика
    """
    # Определяем graph_type: приоритет Excel → base_config → параметр функции
    if rows[0].get('graph_type'):
        actual_graph_type = rows[0]['graph_type']
    elif base_config.get('graph_type'):
        actual_graph_type = base_config['graph_type']
    else:
        actual_graph_type = graph_type

    if len(rows) == 1:
        # Одна строка → одна кривая
        row = rows[0]
        config = ConfigMerger.merge(base_config, row)
        config['type'] = actual_graph_type
        config['output'] = row['output']

        # Оборачиваем в curves в зависимости от типа графика
        if actual_graph_type == 'ode_time':
            curve = {
                'equations': config.get('equations'),
                'variable_names': config.get('variable_names'),
                'initial_conditions': config.get('initial_conditions'),
                'params': config.get('params', {}),
                't_span': config.get('t_span'),
                'styles': config.get('styles'),
                'solver_method': config.get('solver_method'),
                'equilibria': config.get('equilibria')  # ДОБАВЛЕНО: передаем настройки равновесий
            }
            config['curves'] = [curve]

        elif actual_graph_type == 'phase_portrait':
            # Для фазового портрета: style (не styles) + var_indices
            styles = config.get('styles', [{}])
            style = styles[0] if styles else {}

            curve = {
                'equations': config.get('equations'),
                'variable_names': config.get('variable_names'),
                'initial_conditions': config.get('initial_conditions'),
                'params': config.get('params', {}),
                't_span': config.get('t_span'),
                'var_indices': [0, 1],  # по умолчанию s(X) и w(Y)
                'style': style,
                'solver_method': config.get('solver_method')
            }
            config['curves'] = [curve]

            # Для phase_portrait: проверяем, заданы ли границы осей специально для этого графика
            # Если НЕ заданы или заданы неправильно - используем автоматические границы
            if actual_graph_type == 'phase_portrait':
                # Проверяем, явно ли заданы xlim/ylim в Excel для фазового портрета
                # (для phase_portrait: xlim = границы по s, ylim = границы по w)
                xlim_min = row.get('xlim_min')
                xlim_max = row.get('xlim_max')
                ylim_min = row.get('ylim_min')
                ylim_max = row.get('ylim_max')

                # Проверяем, что границы заданы и подходят для фазового портрета
                # xlim: для оси s (должен быть > 20, иначе это границы от ode_time графика)
                # ylim: для оси w (обычно от 0 до 1-5, не больше 50)
                has_valid_xlim = (xlim_min is not None and xlim_max is not None and xlim_max > 20)
                has_valid_ylim = (ylim_min is not None and ylim_max is not None and ylim_max < 50)

                # Если НЕ заданы или неправильные - удаляем для автомасштабирования
                if not has_valid_xlim and 'xlim' in config.get('axes', {}):
                    config['axes']['xlim'] = None
                if not has_valid_ylim and 'ylim' in config.get('axes', {}):
                    config['axes']['ylim'] = None

        # Автоопределение настроек осей на основе созданных кривых
        if 'curves' in config and config['curves']:
            config['axes'] = ConfigMerger.auto_detect_axes_settings(config['curves'], config.get('axes', {}))

    else:
        # Несколько строк → несколько кривых на одном графике
        config = {
            'type': actual_graph_type,
            'output': rows[0]['output'],  # output одинаковый для всех строк в группе
            'curves': []
        }

        # Берем общие настройки из base_config
        config['equations'] = base_config.get('equations')
        config['variable_names'] = base_config.get('variable_names')

        # Обрабатываем axes (из первой строки или base_config)
        # Применяем ConfigMerger._parse_axes для учета xlim_min, xlim_max и т.д. из Excel
        config['axes'] = ConfigMerger._parse_axes(rows[0], base_config.get('axes', {}))

        # Для phase_portrait: проверяем, заданы ли границы осей специально для этого графика
        # Если НЕ заданы или заданы неправильно - используем автоматические границы
        if actual_graph_type == 'phase_portrait':
            first_row = rows[0]

            # Проверяем, явно ли заданы xlim/ylim в Excel для фазового портрета
            # (для phase_portrait: xlim = границы по s, ylim = границы по w)
            xlim_min = first_row.get('xlim_min')
            xlim_max = first_row.get('xlim_max')
            ylim_min = first_row.get('ylim_min')
            ylim_max = first_row.get('ylim_max')

            # Проверяем, что границы заданы и подходят для фазового портрета
            # xlim: для оси s (должен быть > 20, иначе это границы от ode_time графика)
            # ylim: для оси w (обычно от 0 до 1-5, не больше 50)
            has_valid_xlim = (xlim_min is not None and xlim_max is not None and xlim_max > 20)
            has_valid_ylim = (ylim_min is not None and ylim_max is not None and ylim_max < 50)

            # Если НЕ заданы или неправильные - удаляем для автомасштабирования
            if not has_valid_xlim and 'xlim' in config['axes']:
                del config['axes']['xlim']
            if not has_valid_ylim and 'ylim' in config['axes']:
                del config['axes']['ylim']

        # Обрабатываем DPI (из первой строки или base_config)
        if rows[0].get('dpi'):
            config['dpi'] = rows[0]['dpi']
        elif base_config.get('dpi'):
            config['dpi'] = base_config['dpi']

        # Обрабатываем заголовок (из первой строки или base_config)
        if rows[0].get('title'):
            config['title'] = rows[0]['title']
        elif base_config.get('title'):
            config['title'] = base_config['title']

        # Обрабатываем plot_variables (из первой строки или base_config)
        if rows[0].get('plot_variables'):
            config['plot_variables'] = rows[0]['plot_variables']
        elif base_config.get('plot_variables'):
            config['plot_variables'] = base_config['plot_variables']

        # Обрабатываем vector_field для phase_portrait (из первой строки)
        if actual_graph_type == 'phase_portrait':
            first_row = rows[0]
            vector_field_enabled = first_row.get('vector_field_enabled')

            if vector_field_enabled is not None:
                # Преобразуем в bool
                if isinstance(vector_field_enabled, str):
                    enabled = vector_field_enabled.lower() in ('true', 'yes', '1', 'да')
                else:
                    enabled = bool(vector_field_enabled)

                if enabled:
                    vector_field = {
                        'enabled': True,
                        'density': int(first_row.get('vector_field_density', 20)),
                        'color': first_row.get('vector_field_color', 'lightcoral'),
                        'alpha': float(first_row.get('vector_field_alpha', 0.3)),
                        'width': float(first_row.get('vector_field_width', 0.003))
                    }

                    # scale может быть числом или None (для автомасштаба)
                    scale = first_row.get('vector_field_scale')
                    if scale is not None:
                        vector_field['scale'] = float(scale)
                    else:
                        vector_field['scale'] = 30  # значение по умолчанию

                    config['vector_field'] = vector_field

            # Обрабатываем isoclines (изоклины) для phase_portrait
            isoclines_enabled = first_row.get('isoclines_enabled')

            if isoclines_enabled is not None:
                # Преобразуем в bool
                if isinstance(isoclines_enabled, str):
                    enabled = isoclines_enabled.lower() in ('true', 'yes', '1', 'да')
                else:
                    enabled = bool(isoclines_enabled)

                if enabled:
                    isoclines = {
                        'enabled': True,
                        'resolution': int(first_row.get('isoclines_resolution', 200)),
                        'show_ds': first_row.get('isoclines_show_ds', True),
                        'show_dw': first_row.get('isoclines_show_dw', True),
                        'color_ds': first_row.get('isoclines_color_ds', 'blue'),
                        'color_dw': first_row.get('isoclines_color_dw', 'red'),
                        'linestyle_ds': first_row.get('isoclines_linestyle_ds', '-'),
                        'linestyle_dw': first_row.get('isoclines_linestyle_dw', '-'),
                        'linewidth_ds': float(first_row.get('isoclines_linewidth_ds', 2)),
                        'linewidth_dw': float(first_row.get('isoclines_linewidth_dw', 2)),
                        'alpha_ds': float(first_row.get('isoclines_alpha_ds', 0.8)),
                        'alpha_dw': float(first_row.get('isoclines_alpha_dw', 0.8))
                    }

                    # Обработка bool параметров
                    if isinstance(isoclines['show_ds'], str):
                        isoclines['show_ds'] = isoclines['show_ds'].lower() in ('true', 'yes', '1', 'да')
                    else:
                        isoclines['show_ds'] = bool(isoclines['show_ds'])

                    if isinstance(isoclines['show_dw'], str):
                        isoclines['show_dw'] = isoclines['show_dw'].lower() in ('true', 'yes', '1', 'да')
                    else:
                        isoclines['show_dw'] = bool(isoclines['show_dw'])

                    config['isoclines'] = isoclines

        # Создаем кривую для каждой строки
        for row in rows:
            row_config = ConfigMerger.merge(base_config, row)

            if actual_graph_type == 'ode_time':
                curve = {
                    'equations': row_config.get('equations'),
                    'variable_names': row_config.get('variable_names'),
                    'initial_conditions': row_config.get('initial_conditions'),
                    'params': row_config.get('params', {}),
                    't_span': row_config.get('t_span'),
                    'styles': row_config.get('styles'),
                    'solver_method': row_config.get('solver_method'),
                    'equilibria': row_config.get('equilibria')  # ДОБАВЛЕНО: передаем настройки равновесий
                }
                config['curves'].append(curve)

            elif actual_graph_type == 'phase_portrait':
                # Для фазового портрета: style (не styles) + var_indices
                styles = row_config.get('styles', [{}])
                style = styles[0] if styles else {}

                curve = {
                    'equations': row_config.get('equations'),
                    'variable_names': row_config.get('variable_names'),
                    'initial_conditions': row_config.get('initial_conditions'),
                    'params': row_config.get('params', {}),
                    't_span': row_config.get('t_span'),
                    'var_indices': [0, 1],  # по умолчанию s(X) и w(Y)
                    'style': style,
                    'solver_method': row_config.get('solver_method')
                }
                config['curves'].append(curve)

        # Автоопределение настроек осей на основе созданных кривых
        config['axes'] = ConfigMerger.auto_detect_axes_settings(config['curves'], config.get('axes', {}))

    return config


def plot_function(config):
    dpi = config.get('dpi', 300)
    plotter = FunctionPlotter(vars(params_global), dpi=dpi)

    for curve in config['curves']:
        plotter.add_curve_from_latex(
            formula_latex=curve['formula'],      #тип str
            params=curve.get('params', {}),      #словарь, хранит параметры
            x_range=curve['x_range'],            #список, хранить пределы x
            style=curve['style']                 #словарь, хранит информацию о стилях
        )

    axes = config.get('axes', {})                #словарь, или {}
    plotter.set_axes(
        xlim=axes.get('xlim'),                   #[x_min, x_max] или None
        ylim=axes.get('ylim'),                   #[y_min, y_max] или None
        xlabel=axes.get('xlabel', ''),           #str, по умолчанию ''
        ylabel=axes.get('ylabel', ''),           #str, по умолчанию ''
        grid=axes.get('grid', False),            #bool, по умолчанию False, то есть нет сетки по дефолту
        equal_aspect=axes.get('equal_aspect', False), #
        spines=axes.get('spines'),
        grid_style=axes.get('grid_style'),
        axis_labels_at_end=axes.get('axis_labels_at_end', False),
        xticks_minor=axes.get('xticks_minor'),
        yticks_minor=axes.get('yticks_minor')
    )

    # Добавляем горизонтальные линии (асимптоты), если они указаны
    if 'horizontal_lines' in config:
        for line_config in config['horizontal_lines']:
            plotter.add_horizontal_line(
                y=line_config['y'],
                axis=line_config.get('axis', 'left'),
                color=line_config.get('color', 'black'),
                linestyle=line_config.get('linestyle', '-'),
                linewidth=line_config.get('linewidth', 1),
                label=line_config.get('label')
            )

    # Добавляем вертикальные линии (асимптоты), если они указаны
    if 'vertical_lines' in config:
        for line_config in config['vertical_lines']:
            plotter.add_vertical_line(
                x=line_config['x'],
                color=line_config.get('color', 'black'),
                linestyle=line_config.get('linestyle', '-'),
                linewidth=line_config.get('linewidth', 1),
                label=line_config.get('label')
            )

    # Устанавливаем заголовок графика, если он указан в конфигурации
    if 'title' in config:
        plotter.set_title(config['title'])

    #if any('label' in curve['style'] for curve in config['curves']):
    #    plotter.ax.legend()

    output_path = os.path.join('output', config['output']) # сохраняем в output\1
    plotter.save(output_path)                              # сохраняем график в формате SVG
    if not config.get('_silent', False):
        print(f"График создан: {output_path}")


def plot_ode_time(config):
    dpi = config.get('dpi', 300)
    plotter = ODEPlotter(vars(params_global), dpi=dpi)

    # ВАЖНО: Если используется dual_y_axis, создаем вторую ось ДО добавления кривых
    axes = config.get('axes', {})
    if axes.get('dual_y_axis', False):
        plotter.enable_dual_y_axis()

    # Определяем, какие переменные строить
    plot_variables = config.get('plot_variables', 's,w')  # по умолчанию строим обе
    if isinstance(plot_variables, str):
        # Парсим строку: "s", "w", "s,w", "w,s"
        plot_vars_list = [v.strip().lower() for v in plot_variables.split(',')]
    else:
        plot_vars_list = ['s', 'w']  # по умолчанию обе

    # Собираем информацию о равновесиях (список для всех кривых)
    equilibria_info_list = []

    for curve in config['curves']:
        # Фильтруем стили на основе plot_variables
        variable_names = curve['variable_names']
        original_styles = curve['styles']

        # Создаем список стилей с сохранением индексов (None для непостроенных переменных)
        filtered_styles = []
        has_any_variable = False

        for i, var_name in enumerate(variable_names):
            if var_name.lower() in plot_vars_list:
                # Эту переменную нужно строить
                if i < len(original_styles):
                    filtered_styles.append(original_styles[i])
                else:
                    filtered_styles.append({})  # пустой стиль
                has_any_variable = True
            else:
                # Эту переменную НЕ строим - ставим None
                filtered_styles.append(None)

        # Если после фильтрации не осталось переменных для построения, пропускаем кривую
        if not has_any_variable:
            continue

        eq_info = plotter.solve_and_plot_time(
            equations_latex=curve['equations'],
            variable_names=curve['variable_names'],
            initial_conditions=curve['initial_conditions'],
            params=curve.get('params', {}),
            t_span=curve['t_span'],
            style_list=filtered_styles,
            solver_method=curve.get('solver_method'),
            equilibria_config=curve.get('equilibria')
        )

        # Сохраняем информацию о равновесии для этой кривой
        if eq_info:
            equilibria_info_list.append(eq_info)

    plotter.set_axes(
        xlim=axes.get('xlim'),
        ylim=axes.get('ylim'),
        xlabel=axes.get('xlabel', ''),
        ylabel=axes.get('ylabel', ''),
        grid=axes.get('grid', True),
        equal_aspect=axes.get('equal_aspect', False),
        spines=axes.get('spines'),
        grid_style=axes.get('grid_style'),
        axis_labels_at_end=axes.get('axis_labels_at_end', False),
        dual_y_axis=axes.get('dual_y_axis', False),
        ylim_right=axes.get('ylim_right'),
        ylabel_right=axes.get('ylabel_right', ''),
        yticks_right=axes.get('yticks_right'),
        xticks_minor=axes.get('xticks_minor'),
        yticks_minor=axes.get('yticks_minor'),
        yticks_minor_right=axes.get('yticks_minor_right')
    )

    # Добавляем горизонтальные линии (асимптоты), если они указаны
    if 'horizontal_lines' in config:
        for line_config in config['horizontal_lines']:
            plotter.add_horizontal_line(
                y=line_config['y'],
                axis=line_config.get('axis', 'left'),
                color=line_config.get('color', 'black'),
                linestyle=line_config.get('linestyle', '-'),
                linewidth=line_config.get('linewidth', 1),
                label=line_config.get('label')
            )

    # Добавляем вертикальные линии (асимптоты), если они указаны
    if 'vertical_lines' in config:
        for line_config in config['vertical_lines']:
            plotter.add_vertical_line(
                x=line_config['x'],
                color=line_config.get('color', 'black'),
                linestyle=line_config.get('linestyle', '-'),
                linewidth=line_config.get('linewidth', 1),
                label=line_config.get('label')
            )

    # Устанавливаем заголовок графика, если он указан в конфигурации
    if 'title' in config:
        plotter.set_title(config['title'])

    output_path = os.path.join('output', config['output'])
    plotter.save(output_path)
    if not config.get('_silent', False):
        print(f"График создан: {output_path}")

    # Возвращаем список информации о равновесиях с именем файла
    if equilibria_info_list:
        for eq_info in equilibria_info_list:
            eq_info['output'] = config['output']
            eq_info['type'] = 'ode_time'
        return equilibria_info_list
    return None


def plot_phase_portrait(config):
    dpi = config.get('dpi', 300)
    plotter = ODEPlotter(vars(params_global), dpi=dpi)

    # Сначала установить пределы осей
    axes = config.get('axes', {})
    if axes.get('xlim') and axes.get('ylim'):
        plotter.ax.set_xlim(axes['xlim'])
        plotter.ax.set_ylim(axes['ylim'])

    # Затем построить векторное поле (если есть)
    vector_field = config.get('vector_field')
    if vector_field and vector_field.get('enabled', False):
        first_curve = config['curves'][0]
        plotter.add_vector_field(
            equations_latex=first_curve['equations'],
            variable_names=first_curve['variable_names'],
            params=first_curve.get('params', {}),
            var_indices=first_curve['var_indices'],
            field_config=vector_field
        )

    # Построить изоклины (нуль-клины) - линии, где ds/dt=0 и dw/dt=0
    isoclines = config.get('isoclines')
    if isoclines and isoclines.get('enabled', False):
        first_curve = config['curves'][0]
        plotter.add_isoclines(
            equations_latex=first_curve['equations'],
            variable_names=first_curve['variable_names'],
            params=first_curve.get('params', {}),
            var_indices=first_curve['var_indices'],
            isocline_config=isoclines
        )

    # Собираем информацию о равновесиях (список для всех кривых)
    equilibria_info_list = []

    # Построить траектории
    for curve in config['curves']:
        plotter.solve_and_plot_phase(
            equations_latex=curve['equations'],
            variable_names=curve['variable_names'],
            initial_conditions=curve['initial_conditions'],
            params=curve.get('params', {}),
            t_span=curve['t_span'],
            var_indices=curve['var_indices'],
            style=curve['style'],
            solver_method=curve.get('solver_method')
        )

        # Для фазового портрета: ВСЕГДА найти равновесие и проанализировать устойчивость
        # НЕ рисуем горизонтальные линии (show=False), только анализируем и пишем в файл
        # Получаем конфиг из curve или создаем дефолтный
        equilibria_config = curve.get('equilibria', {})

        # Если конфига нет - создаем дефолтный для анализа фазовых портретов
        if not equilibria_config:
            equilibria_config = {
                'refine': True,
                's': {'show': False},
                'w': {'show': False}
            }

        # Отключаем отрисовку (гарантируем что ничего не рисуется на графике)
        temp_config = equilibria_config.copy()
        for var in ['s', 'w']:
            if var not in temp_config:
                temp_config[var] = {}
            if not isinstance(temp_config[var], dict):
                temp_config[var] = {}
            temp_config[var]['show'] = False

        # Находим равновесие с анализом устойчивости
        try:
            system = ODESystem(curve['equations'], curve['variable_names'])
            merged_params = merge_params(vars(params_global), curve.get('params', {}))
            param_values = [merged_params[str(p)] for p in system.params]

            eq_info = plotter._add_equilibria(
                system, curve['variable_names'], curve['initial_conditions'],
                param_values, curve['t_span'], temp_config,
                analyze_stability=True
            )

            # Добавляем в список если нашли равновесие
            if eq_info:
                equilibria_info_list.append(eq_info)
        except Exception as e:
            # Если анализ равновесия не удался, просто пропускаем
            print(f"Warning: Could not analyze equilibrium for phase portrait: {e}")

    plotter.set_axes(
        xlim=axes.get('xlim'),
        ylim=axes.get('ylim'),
        xlabel=axes.get('xlabel', ''),
        ylabel=axes.get('ylabel', ''),
        grid=axes.get('grid', True),
        equal_aspect=axes.get('equal_aspect', False),
        spines=axes.get('spines'),
        grid_style=axes.get('grid_style'),
        xticks=axes.get('xticks'),
        yticks=axes.get('yticks'),
        axis_labels_at_end=axes.get('axis_labels_at_end', False),
        xticks_minor=axes.get('xticks_minor'),
        yticks_minor=axes.get('yticks_minor')
    )

    # Добавляем горизонтальные линии (асимптоты), если они указаны
    if 'horizontal_lines' in config:
        for line_config in config['horizontal_lines']:
            plotter.add_horizontal_line(
                y=line_config['y'],
                axis=line_config.get('axis', 'left'),
                color=line_config.get('color', 'black'),
                linestyle=line_config.get('linestyle', '-'),
                linewidth=line_config.get('linewidth', 1),
                label=line_config.get('label')
            )

    # Добавляем вертикальные линии (асимптоты), если они указаны
    if 'vertical_lines' in config:
        for line_config in config['vertical_lines']:
            plotter.add_vertical_line(
                x=line_config['x'],
                color=line_config.get('color', 'black'),
                linestyle=line_config.get('linestyle', '-'),
                linewidth=line_config.get('linewidth', 1),
                label=line_config.get('label')
            )

    # Устанавливаем заголовок графика, если он указан в конфигурации
    if 'title' in config:
        plotter.set_title(config['title'])

    output_path = os.path.join('output', config['output'])
    plotter.save(output_path)
    if not config.get('_silent', False):
        print(f"График создан: {output_path}")

    # Возвращаем список информации о равновесиях с именем файла
    if equilibria_info_list:
        for eq_info in equilibria_info_list:
            eq_info['output'] = config['output']
            eq_info['type'] = 'phase_portrait'
        return equilibria_info_list
    return None


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='Построение графиков из YAML конфигурации')
    parser.add_argument('--config', required=True, help='Путь к YAML файлу конфигурации')

    args = parser.parse_args()

    config = load_config(args.config)
    plot_from_config(config)