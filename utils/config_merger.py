import copy
from typing import Dict, List, Any


class ConfigMerger:
    """
    Объединение базового конфига из YAML с параметрами из строки Excel

    Логика слияния:
    1. Начинаем с глубокой копии base_config
    2. Параметры из row_params переопределяют базовые
    3. Специальные колонки (s0, w0, color_s и т.д.) преобразуются в нужную структуру
    4. Приоритет: Excel > YAML > defaults
    """

    @staticmethod
    def merge(base_config: Dict, row_params: Dict) -> Dict:
        """
        Объединяет базовый конфиг с параметрами из строки Excel

        Параметры:
        - base_config: базовая конфигурация из YAML
        - row_params: параметры из строки Excel (словарь)

        Возвращает:
        - Объединенная конфигурация для построения графика
        """
        # Глубокая копия базового конфига, чтобы не модифицировать оригинал
        config = copy.deepcopy(base_config)

        # 0. Обработка уравнений (equation_1, equation_2) - ПРИОРИТЕТ!
        # Если в Excel указаны уравнения, они полностью заменяют базовые
        equations = ConfigMerger._parse_equations(row_params, config.get('equations'))
        if equations:
            config['equations'] = equations

        # 1. Обработка параметров системы (a, alpha, h, и т.д.)
        params = ConfigMerger._parse_params(row_params, config.get('params', {}))
        if params:
            config['params'] = params

        # 2. Обработка начальных условий (s0, w0)
        initial_conditions = ConfigMerger._parse_initial_conditions(
            row_params,
            config.get('initial_conditions', [300, 0.5])
        )
        if initial_conditions:
            config['initial_conditions'] = initial_conditions

        # 3. Обработка временного интервала (t_start, t_end)
        t_span = ConfigMerger._parse_t_span(
            row_params,
            config.get('t_span', [0, 7])
        )
        if t_span:
            config['t_span'] = t_span

        # 4. Обработка стилей (color_s, linestyle_s, color_w, linestyle_w и т.д.)
        styles = ConfigMerger._parse_styles(
            row_params,
            config.get('styles', [])
        )
        if styles:
            config['styles'] = styles

        # 5. Обработка настроек осей (xlim_min, xlim_max и т.д.)
        axes = ConfigMerger._parse_axes(
            row_params,
            config.get('axes', {})
        )
        if axes:
            config['axes'] = axes

        # 6. Обработка заголовка
        if row_params.get('title'):
            config['title'] = row_params['title']

        # 7. Обработка выходного файла
        if row_params.get('output'):
            config['output'] = row_params['output']

        # 8. Обработка метода решения
        solver_method = row_params.get('solver_method')
        if solver_method and isinstance(solver_method, str):
            config['solver_method'] = solver_method

        # 9. Обработка DPI
        if row_params.get('dpi'):
            config['dpi'] = row_params['dpi']

        # 10. Обработка plot_variables (какие переменные строить)
        if row_params.get('plot_variables'):
            config['plot_variables'] = row_params['plot_variables']

        # 11. Обработка graph_type (тип графика: ode_time, phase_portrait)
        if row_params.get('graph_type'):
            config['graph_type'] = row_params['graph_type']

        # 12. Обработка настроек равновесий/асимптот
        equilibria = ConfigMerger._parse_equilibrium_settings(
            row_params,
            config.get('equilibria', {})
        )
        if equilibria:
            config['equilibria'] = equilibria

        return config

    @staticmethod
    def _parse_equations(row_params: Dict, base_equations: List) -> List:
        """
        Обрабатывает уравнения из колонок equation_1, equation_2, ...

        Если в Excel указаны equation_1, equation_2 и т.д., они полностью заменяют
        базовые уравнения из YAML.

        Поддерживает:
        - equation_1 → первое уравнение (обычно ds/dt)
        - equation_2 → второе уравнение (обычно dw/dt)
        - equation_3, equation_4, ... → для систем с большим числом переменных

        Приоритет:
        1. Уравнения из Excel (equation_1, equation_2, ...)
        2. Базовые уравнения из YAML

        Возвращает:
        - Список уравнений или None (если уравнения не заменяются)
        """
        # Проверяем наличие хотя бы одного equation_*
        has_equations = any(key.startswith('equation_') for key in row_params.keys() if row_params.get(key))

        if not has_equations:
            # Нет уравнений в Excel → используем базовые
            return None

        # Собираем уравнения из equation_1, equation_2, equation_3, ...
        equations = []

        # Пытаемся найти equation_1, equation_2, ... до первого пропуска
        index = 1
        while True:
            eq_key = f'equation_{index}'
            if eq_key in row_params and row_params[eq_key] is not None and str(row_params[eq_key]).strip():
                equations.append(str(row_params[eq_key]).strip())
                index += 1
            else:
                # Если нет equation_N, прерываем
                break

        # Если не нашли ни одного уравнения, используем базовые
        if not equations:
            return None

        return equations

    @staticmethod
    def _parse_params(row_params: Dict, base_params: Dict) -> Dict:
        """
        Обрабатывает параметры системы (a, alpha, h, b, c и т.д.)

        Параметры из row_params с известными именами переопределяют base_params
        """
        params = copy.deepcopy(base_params)

        # Список известных параметров системы
        known_params = ['a', 'alpha', 'betta', 'b', 'c', 'h']

        for param in known_params:
            if param in row_params and row_params[param] is not None:
                params[param] = row_params[param]

        return params

    @staticmethod
    def _parse_initial_conditions(row_params: Dict, base_ic: List) -> List:
        """
        Обрабатывает начальные условия из колонок s0, w0

        Приоритет:
        1. s0, w0 из Excel
        2. base_ic из YAML
        """
        ic = list(base_ic)  # копируем базовые

        # s0 → initial_conditions[0]
        if 's0' in row_params and row_params['s0'] is not None:
            ic[0] = row_params['s0']

        # w0 → initial_conditions[1]
        if 'w0' in row_params and row_params['w0'] is not None:
            if len(ic) < 2:
                ic.append(row_params['w0'])
            else:
                ic[1] = row_params['w0']

        return ic

    @staticmethod
    def _parse_t_span(row_params: Dict, base_t_span: List) -> List:
        """
        Обрабатывает временной интервал из колонок t_start, t_end

        Приоритет:
        1. t_start, t_end из Excel
        2. base_t_span из YAML
        """
        t_span = list(base_t_span)  # копируем базовые

        # t_start → t_span[0]
        if 't_start' in row_params and row_params['t_start'] is not None:
            t_span[0] = row_params['t_start']

        # t_end → t_span[1]
        if 't_end' in row_params and row_params['t_end'] is not None:
            if len(t_span) < 2:
                t_span.append(row_params['t_end'])
            else:
                t_span[1] = row_params['t_end']

        return t_span

    @staticmethod
    def _parse_styles(row_params: Dict, base_styles: List) -> List:
        """
        Обрабатывает стили из колонок color_s, linestyle_s, linewidth_s, label_s
        и color_w, linestyle_w, linewidth_w, label_w

        Для ode_time обычно 2 стиля: [style_s, style_w]
        """
        # Глубокая копия базовых стилей
        styles = copy.deepcopy(base_styles)

        # Убедимся, что есть минимум 2 стиля (для s и w)
        while len(styles) < 2:
            styles.append({})

        # Проверяем plot_variables - какие переменные нужно рисовать
        plot_vars = row_params.get('plot_variables', 's,w')
        if isinstance(plot_vars, str):
            plot_vars = plot_vars.strip().lower()
            plot_s = 's' in plot_vars
            plot_w = 'w' in plot_vars
        else:
            plot_s = True
            plot_w = True

        # Стиль для s (первый элемент styles[0])
        if plot_s:
            if 'color_s' in row_params and row_params['color_s'] is not None:
                styles[0]['color'] = row_params['color_s']
            if 'linestyle_s' in row_params and row_params['linestyle_s'] is not None:
                styles[0]['linestyle'] = row_params['linestyle_s']
            if 'linewidth_s' in row_params and row_params['linewidth_s'] is not None:
                styles[0]['linewidth'] = row_params['linewidth_s']
            if 'label_s' in row_params and row_params['label_s'] is not None:
                styles[0]['label'] = row_params['label_s']

            # Параметры стрелок для фазовых портретов (применяются к styles[0])
            if 'show_arrows' in row_params and row_params['show_arrows'] is not None:
                # Принимаем True/False, "true"/"false", 1/0, "yes"/"no"
                val = row_params['show_arrows']
                if isinstance(val, str):
                    styles[0]['show_arrows'] = val.lower() in ('true', 'yes', '1', 'да')
                else:
                    styles[0]['show_arrows'] = bool(val)
            if 'num_arrows' in row_params and row_params['num_arrows'] is not None:
                styles[0]['num_arrows'] = int(row_params['num_arrows'])
            if 'arrow_size' in row_params and row_params['arrow_size'] is not None:
                styles[0]['arrow_size'] = float(row_params['arrow_size'])
        else:
            # Если s не рисуем, устанавливаем стиль в None
            styles[0] = None

        # Стиль для w (второй элемент styles[1])
        if plot_w:
            if 'color_w' in row_params and row_params['color_w'] is not None:
                styles[1]['color'] = row_params['color_w']
            if 'linestyle_w' in row_params and row_params['linestyle_w'] is not None:
                styles[1]['linestyle'] = row_params['linestyle_w']
            if 'linewidth_w' in row_params and row_params['linewidth_w'] is not None:
                styles[1]['linewidth'] = row_params['linewidth_w']
            if 'label_w' in row_params and row_params['label_w'] is not None:
                styles[1]['label'] = row_params['label_w']

            # use_right_axis для w должен остаться, если был в base_styles
            # (не переопределяется из Excel)
        else:
            # Если w не рисуем, устанавливаем стиль в None
            styles[1] = None

        return styles

    @staticmethod
    def _parse_axes(row_params: Dict, base_axes: Dict) -> Dict:
        """
        Обрабатывает настройки осей из колонок xlim_min, xlim_max, ylim_min, ylim_max и т.д.

        Параметры:
        - xlim_min, xlim_max → axes.xlim
        - ylim_min, ylim_max → axes.ylim
        - ylim_right_min, ylim_right_max → axes.ylim_right
        """
        axes = copy.deepcopy(base_axes)

        # xlim
        xlim = axes.get('xlim', [None, None])
        if 'xlim_min' in row_params and row_params['xlim_min'] is not None:
            xlim[0] = row_params['xlim_min']
        if 'xlim_max' in row_params and row_params['xlim_max'] is not None:
            if len(xlim) < 2:
                xlim.append(row_params['xlim_max'])
            else:
                xlim[1] = row_params['xlim_max']
        if xlim[0] is not None or xlim[1] is not None:
            axes['xlim'] = xlim

        # ylim (левая ось)
        ylim = axes.get('ylim', [None, None])
        if 'ylim_min' in row_params and row_params['ylim_min'] is not None:
            ylim[0] = row_params['ylim_min']
        if 'ylim_max' in row_params and row_params['ylim_max'] is not None:
            if len(ylim) < 2:
                ylim.append(row_params['ylim_max'])
            else:
                ylim[1] = row_params['ylim_max']
        if ylim[0] is not None or ylim[1] is not None:
            axes['ylim'] = ylim

        # ylim_right (правая ось)
        ylim_right = axes.get('ylim_right', [None, None])
        if 'ylim_right_min' in row_params and row_params['ylim_right_min'] is not None:
            ylim_right[0] = row_params['ylim_right_min']
        if 'ylim_right_max' in row_params and row_params['ylim_right_max'] is not None:
            if len(ylim_right) < 2:
                ylim_right.append(row_params['ylim_right_max'])
            else:
                ylim_right[1] = row_params['ylim_right_max']
        if ylim_right[0] is not None or ylim_right[1] is not None:
            axes['ylim_right'] = ylim_right

        # Парсинг меток (ticks) из строк через ";"
        # xticks и xticks_minor
        if 'xticks' in row_params and row_params['xticks'] is not None:
            xticks_str = str(row_params['xticks']).strip()
            if xticks_str:
                axes['xticks'] = [float(x.strip()) for x in xticks_str.split(';') if x.strip()]

        if 'xticks_minor' in row_params and row_params['xticks_minor'] is not None:
            xticks_minor_str = str(row_params['xticks_minor']).strip()
            if xticks_minor_str:
                axes['xticks_minor'] = [float(x.strip()) for x in xticks_minor_str.split(';') if x.strip()]

        # yticks и yticks_minor (левая ось)
        if 'yticks' in row_params and row_params['yticks'] is not None:
            yticks_str = str(row_params['yticks']).strip()
            if yticks_str:
                axes['yticks'] = [float(y.strip()) for y in yticks_str.split(';') if y.strip()]

        if 'yticks_minor' in row_params and row_params['yticks_minor'] is not None:
            yticks_minor_str = str(row_params['yticks_minor']).strip()
            if yticks_minor_str:
                axes['yticks_minor'] = [float(y.strip()) for y in yticks_minor_str.split(';') if y.strip()]

        # yticks_right и yticks_minor_right (правая ось)
        if 'yticks_right' in row_params and row_params['yticks_right'] is not None:
            yticks_right_str = str(row_params['yticks_right']).strip()
            if yticks_right_str:
                axes['yticks_right'] = [float(y.strip()) for y in yticks_right_str.split(';') if y.strip()]

        if 'yticks_minor_right' in row_params and row_params['yticks_minor_right'] is not None:
            yticks_minor_right_str = str(row_params['yticks_minor_right']).strip()
            if yticks_minor_right_str:
                axes['yticks_minor_right'] = [float(y.strip()) for y in yticks_minor_right_str.split(';') if y.strip()]

        return axes

    @staticmethod
    def auto_detect_axes_settings(curves_data: list, base_axes: Dict) -> Dict:
        """
        Автоматически определяет настройки осей на основе данных кривых.

        Параметры:
        - curves_data: список данных кривых (каждая содержит 'styles' или 'style')
        - base_axes: базовые настройки осей из YAML

        Возвращает:
        - Обновлённые настройки axes с dual_y_axis и spines

        Логика:
        1. Проверяет наличие use_right_axis: true в стилях кривых
        2. Если есть хотя бы один → dual_y_axis = true, right spine = true
        3. Иначе → dual_y_axis = false, right spine = false
        """
        axes = copy.deepcopy(base_axes)

        # Проверяем, есть ли кривые с правой осью
        has_right_axis = False

        for curve_data in curves_data:
            # Для ode_time: styles - список
            if 'styles' in curve_data:
                styles = curve_data['styles']
                if isinstance(styles, list):
                    for style in styles:
                        if isinstance(style, dict) and style.get('use_right_axis', False):
                            has_right_axis = True
                            break

            # Для phase_portrait: style - словарь
            if 'style' in curve_data:
                style = curve_data['style']
                if isinstance(style, dict) and style.get('use_right_axis', False):
                    has_right_axis = True

            if has_right_axis:
                break

        # Устанавливаем dual_y_axis
        axes['dual_y_axis'] = has_right_axis

        # Автоматически генерируем spines
        if has_right_axis:
            # Две оси: показываем правую и нижнюю рамки
            axes['spines'] = {
                'top': False,
                'right': True,
                'bottom': True,
                'left': True
            }
        else:
            # Одна ось: скрываем правую рамку
            axes['spines'] = {
                'top': False,
                'right': False,
                'bottom': True,
                'left': True
            }

        return axes

    @staticmethod
    def _parse_equilibrium_settings(row_params: Dict, base_equilibria: Dict) -> Dict:
        """
        Обрабатывает настройки отображения равновесий/асимптот из Excel.

        Колонки в Excel:
        ----------------
        Для переменной s:
        - equilibrium_s_show: показывать ли асимптоту для s (True/False)
        - equilibrium_s_linestyle: стиль линии ('-', '--', '-.', ':')
        - equilibrium_s_color: цвет линии
        - equilibrium_s_linewidth: толщина линии
        - equilibrium_s_alpha: прозрачность (0-1)
        - equilibrium_s_label: текст метки (опционально)

        Для переменной w:
        - equilibrium_w_show
        - equilibrium_w_linestyle
        - equilibrium_w_color
        - equilibrium_w_linewidth
        - equilibrium_w_alpha
        - equilibrium_w_label

        Общие настройки (опционально):
        - equilibrium_t_max: время интегрирования (по умолчанию авто: t_график × 10)
        - equilibrium_refine: уточнять ли через оптимизацию (True/False, по умолчанию True)

        Параметры:
        ----------
        row_params : dict
            Параметры из строки Excel
        base_equilibria : dict
            Базовые настройки из YAML

        Возвращает:
        -----------
        equilibria : dict
            Настройки равновесий:
            {
                's': {
                    'show': True,
                    'linestyle': '--',
                    'color': 'red',
                    'linewidth': 1.5,
                    'alpha': 0.7,
                    'label': 's*'
                },
                'w': {
                    'show': True,
                    'linestyle': '--',
                    'color': 'blue',
                    'linewidth': 1.5,
                    'alpha': 0.7,
                    'label': 'w*'
                },
                't_max': 1000.0,
                'refine': True
            }
        """
        # Глубокая копия базовых настроек
        equilibria = copy.deepcopy(base_equilibria)

        # Обеспечиваем наличие структуры для s и w
        if 's' not in equilibria:
            equilibria['s'] = {}
        if 'w' not in equilibria:
            equilibria['w'] = {}

        # Парсинг настроек для переменной s
        if 'equilibrium_s_show' in row_params and row_params['equilibrium_s_show'] is not None:
            val = row_params['equilibrium_s_show']
            if isinstance(val, str):
                equilibria['s']['show'] = val.lower() in ('true', 'yes', '1', 'да')
            else:
                equilibria['s']['show'] = bool(val)

        if 'equilibrium_s_linestyle' in row_params and row_params['equilibrium_s_linestyle'] is not None:
            equilibria['s']['linestyle'] = row_params['equilibrium_s_linestyle']

        if 'equilibrium_s_color' in row_params and row_params['equilibrium_s_color'] is not None:
            equilibria['s']['color'] = row_params['equilibrium_s_color']

        if 'equilibrium_s_linewidth' in row_params and row_params['equilibrium_s_linewidth'] is not None:
            equilibria['s']['linewidth'] = float(row_params['equilibrium_s_linewidth'])

        if 'equilibrium_s_alpha' in row_params and row_params['equilibrium_s_alpha'] is not None:
            equilibria['s']['alpha'] = float(row_params['equilibrium_s_alpha'])

        if 'equilibrium_s_label' in row_params and row_params['equilibrium_s_label'] is not None:
            equilibria['s']['label'] = row_params['equilibrium_s_label']

        # Парсинг настроек для переменной w
        if 'equilibrium_w_show' in row_params and row_params['equilibrium_w_show'] is not None:
            val = row_params['equilibrium_w_show']
            if isinstance(val, str):
                equilibria['w']['show'] = val.lower() in ('true', 'yes', '1', 'да')
            else:
                equilibria['w']['show'] = bool(val)

        if 'equilibrium_w_linestyle' in row_params and row_params['equilibrium_w_linestyle'] is not None:
            equilibria['w']['linestyle'] = row_params['equilibrium_w_linestyle']

        if 'equilibrium_w_color' in row_params and row_params['equilibrium_w_color'] is not None:
            equilibria['w']['color'] = row_params['equilibrium_w_color']

        if 'equilibrium_w_linewidth' in row_params and row_params['equilibrium_w_linewidth'] is not None:
            equilibria['w']['linewidth'] = float(row_params['equilibrium_w_linewidth'])

        if 'equilibrium_w_alpha' in row_params and row_params['equilibrium_w_alpha'] is not None:
            equilibria['w']['alpha'] = float(row_params['equilibrium_w_alpha'])

        if 'equilibrium_w_label' in row_params and row_params['equilibrium_w_label'] is not None:
            equilibria['w']['label'] = row_params['equilibrium_w_label']

        # Общие настройки
        if 'equilibrium_t_max' in row_params and row_params['equilibrium_t_max'] is not None:
            equilibria['t_max'] = float(row_params['equilibrium_t_max'])

        if 'equilibrium_refine' in row_params and row_params['equilibrium_refine'] is not None:
            val = row_params['equilibrium_refine']
            if isinstance(val, str):
                equilibria['refine'] = val.lower() in ('true', 'yes', '1', 'да')
            else:
                equilibria['refine'] = bool(val)

        return equilibria
