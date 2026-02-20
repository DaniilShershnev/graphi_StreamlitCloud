from core.base_plotter import GraphPlotter
from models.ode_system import ODESystem
from utils.validators import merge_params
from scipy.integrate import solve_ivp
import numpy as np


class ODEPlotter(GraphPlotter):
    def __init__(self, global_params, dpi=300):
        super().__init__(dpi=dpi)
        self.global_params = global_params

    def solve_and_plot_time(self, equations_latex, variable_names, initial_conditions, params, t_span, style_list, solver_method=None, equilibria_config=None):
        system = ODESystem(equations_latex, variable_names)

        merged_params = merge_params(self.global_params, params)

        param_values = [merged_params[str(p)] for p in system.params]

        t_span_use = merged_params.get('t_span', t_span)
        rtol = merged_params.get('rtol', 1e-9)
        atol = merged_params.get('atol', 1e-12)
        n_points = merged_params.get('n_points', 1000)
        # LSODA автоматически переключается между stiff/non-stiff методами
        method = solver_method or merged_params.get('default_solver_method', 'LSODA')

        t_eval = np.linspace(t_span_use[0], t_span_use[1], n_points)

        sol = solve_ivp(
            lambda t, y: system.right_hand_side(t, y, param_values),
            t_span_use,
            initial_conditions,
            method=method,
            rtol=rtol,
            atol=atol,
            t_eval=t_eval,
            max_step=(t_span_use[1] - t_span_use[0]) / 100  # Ограничиваем шаг для стабильности
        )

        for i, style in enumerate(style_list):
            # Пропускаем переменные со стилем None (не нужно строить)
            if style is None:
                continue

            # Проверяем, нужно ли рисовать на правой оси
            if isinstance(style, dict):
                use_right_axis = style.get('use_right_axis', False)
                # Создаем копию стиля без параметра use_right_axis (он не нужен для plot)
                plot_style = {k: v for k, v in style.items() if k != 'use_right_axis'}
            else:
                use_right_axis = False
                plot_style = style
            self.add_curve(sol.t, sol.y[i], plot_style, use_right_axis=use_right_axis)

        # Добавляем равновесия/асимптоты если включено
        equilibria_info = None
        if equilibria_config:
            equilibria_info = self._add_equilibria(system, variable_names, initial_conditions, param_values, t_span_use, equilibria_config, analyze_stability=False)

        return equilibria_info

    def solve_and_plot_phase(self, equations_latex, variable_names, initial_conditions, params, t_span, var_indices,
                             style, solver_method=None):
        system = ODESystem(equations_latex, variable_names)

        merged_params = merge_params(self.global_params, params)

        param_values = [merged_params[str(p)] for p in system.params]

        t_span_use = merged_params.get('t_span', t_span)
        rtol = merged_params.get('rtol', 1e-9)
        atol = merged_params.get('atol', 1e-12)
        n_points = merged_params.get('n_points', 1000)
        # LSODA автоматически переключается между stiff/non-stiff методами
        method = solver_method or merged_params.get('default_solver_method', 'LSODA')

        t_eval = np.linspace(t_span_use[0], t_span_use[1], n_points)

        sol = solve_ivp(
            lambda t, y: system.right_hand_side(t, y, param_values),
            t_span_use,
            initial_conditions,
            method=method,
            rtol=rtol,
            atol=atol,
            t_eval=t_eval,
            max_step=(t_span_use[1] - t_span_use[0]) / 100  # Ограничиваем шаг для стабильности
        )

        x_var = sol.y[var_indices[0]]
        y_var = sol.y[var_indices[1]]

        # Извлекаем параметры стрелок из style (они не должны попасть в matplotlib)
        show_arrows = style.pop('show_arrows', False)
        num_arrows = style.pop('num_arrows', 3)
        arrow_size = style.pop('arrow_size', 10)

        # Добавляем траекторию
        self.add_curve(x_var, y_var, style)

        # Добавляем стрелки, если указано в стиле
        if show_arrows:
            color = style.get('color', 'black')
            self.add_arrows_to_curve(x_var, y_var, color=color, num_arrows=num_arrows, arrow_size=arrow_size)

    def add_vector_field(self, equations_latex, variable_names, params, var_indices, field_config):
        from models.ode_system import ODESystem
        import numpy as np
        import warnings

        system = ODESystem(equations_latex, variable_names)

        merged_params = merge_params(self.global_params, params)
        param_values = [merged_params[str(p)] for p in system.params]

        # Получить пределы осей
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Создать сетку точек
        density = field_config.get('density', 20)
        x_grid = np.linspace(xlim[0], xlim[1], density)
        y_grid = np.linspace(ylim[0], ylim[1], density)
        X, Y = np.meshgrid(x_grid, y_grid)

        # Вычислить векторы направлений
        U = np.zeros_like(X)
        V = np.zeros_like(Y)

        # Подавляем warnings о делении на ноль (нормально для векторных полей)
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)

            for i in range(density):
                for j in range(density):
                    state = [0] * len(variable_names)
                    state[var_indices[0]] = X[i, j]
                    state[var_indices[1]] = Y[i, j]

                    derivatives = system.right_hand_side(0, state, param_values)
                    U[i, j] = derivatives[var_indices[0]]
                    V[i, j] = derivatives[var_indices[1]]

        # Нормализация с учетом масштаба осей
        x_scale = xlim[1] - xlim[0]
        y_scale = ylim[1] - ylim[0]

        # Масштабируем векторы пропорционально диапазону осей
        U_scaled = U / x_scale
        V_scaled = V / y_scale

        # Нормализуем - все стрелки одинаковой длины
        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)
            magnitude = np.sqrt(U_scaled ** 2 + V_scaled ** 2)
            magnitude[magnitude == 0] = 1  # избежать деления на 0
            U_norm = U_scaled / magnitude
            V_norm = V_scaled / magnitude

        # Построить векторное поле
        self.ax.quiver(
            X, Y, U_norm, V_norm,
            color=field_config.get('color', 'pink'),
            alpha=field_config.get('alpha', 0.3),
            scale=field_config.get('scale', 30),
            width=field_config.get('width', 0.003),
            headwidth=3,
            headlength=4
        )

    def add_isoclines(self, equations_latex, variable_names, params, var_indices, isocline_config):
        """
        Добавляет изоклины (нуль-клины) на фазовый портрет

        Изоклины - это линии, на которых производная одной из переменных равна нулю:
        - ds/dt = 0 (изоклина для s)
        - dw/dt = 0 (изоклина для w)

        Параметры:
        - equations_latex: список уравнений системы в LaTeX
        - variable_names: список имен переменных
        - params: параметры системы
        - var_indices: индексы переменных для фазового портрета [index_s, index_w]
        - isocline_config: конфигурация изоклин (цвета, стили и т.д.)
        """
        from models.ode_system import ODESystem
        import numpy as np
        import warnings

        system = ODESystem(equations_latex, variable_names)

        merged_params = merge_params(self.global_params, params)
        param_values = [merged_params[str(p)] for p in system.params]

        # Получить пределы осей
        xlim = self.ax.get_xlim()
        ylim = self.ax.get_ylim()

        # Создать сетку точек
        resolution = isocline_config.get('resolution', 200)
        x_grid = np.linspace(xlim[0], xlim[1], resolution)
        y_grid = np.linspace(ylim[0], ylim[1], resolution)
        X, Y = np.meshgrid(x_grid, y_grid)

        # Вычислить производные для каждой точки сетки
        dS = np.zeros_like(X)
        dW = np.zeros_like(Y)

        with warnings.catch_warnings():
            warnings.filterwarnings('ignore', category=RuntimeWarning)

            for i in range(resolution):
                for j in range(resolution):
                    state = [0] * len(variable_names)
                    state[var_indices[0]] = X[i, j]
                    state[var_indices[1]] = Y[i, j]

                    derivatives = system.right_hand_side(0, state, param_values)
                    dS[i, j] = derivatives[var_indices[0]]
                    dW[i, j] = derivatives[var_indices[1]]

        # Построить изоклину ds/dt = 0
        if isocline_config.get('show_ds', True):
            self.ax.contour(
                X, Y, dS, levels=[0],
                colors=[isocline_config.get('color_ds', 'blue')],
                linestyles=[isocline_config.get('linestyle_ds', '-')],
                linewidths=[isocline_config.get('linewidth_ds', 2)],
                alpha=isocline_config.get('alpha_ds', 0.8)
            )

        # Построить изоклину dw/dt = 0
        if isocline_config.get('show_dw', True):
            self.ax.contour(
                X, Y, dW, levels=[0],
                colors=[isocline_config.get('color_dw', 'red')],
                linestyles=[isocline_config.get('linestyle_dw', '-')],
                linewidths=[isocline_config.get('linewidth_dw', 2)],
                alpha=isocline_config.get('alpha_dw', 0.8)
            )

    def _add_equilibria(self, system, variable_names, initial_conditions, param_values, t_span, equilibria_config, analyze_stability=False):
        """
        Находит и отрисовывает равновесия системы (асимптоты)

        Параметры:
        - system: объект ODESystem
        - variable_names: список имен переменных ['s', 'w']
        - initial_conditions: начальные условия [s0, w0]
        - param_values: значения параметров системы
        - t_span: временной интервал
        - equilibria_config: настройки отображения равновесий
        - analyze_stability: нужен ли анализ устойчивости (для фазовых портретов)

        Возвращает:
        - Dict с информацией о равновесии или None если не найдено
        """
        from utils.equilibrium_finder import EquilibriumFinder

        # Создаем ODE функцию для finder
        def ode_func(t, y, params_dict):
            return np.array(system.right_hand_side(t, y, param_values))

        # Автоматически выбираем время интегрирования для поиска равновесия
        # Используем в 10 раз больше чем время графика, минимум 100
        t_graph_end = t_span[1] if isinstance(t_span, (list, tuple)) else t_span
        t_max_auto = max(t_graph_end * 10, 100.0)

        # Получаем настройки поиска (можно переопределить t_max вручную если нужно)
        t_max = equilibria_config.get('t_max', t_max_auto)
        refine = equilibria_config.get('refine', True)

        # Создаем finder и ищем равновесие
        finder = EquilibriumFinder(ode_func, convergence_threshold=1e-6)
        result = finder.find_equilibrium(
            y0=np.array(initial_conditions),
            params={},  # параметры уже в param_values
            t_max=t_max,
            refine=refine
        )

        equilibrium = result['equilibrium']
        converged = result['converged']

        # Подготовим информацию для возврата
        result_info = {
            's_star': float(equilibrium[0]) if len(equilibrium) > 0 else None,
            'w_star': float(equilibrium[1]) if len(equilibrium) > 1 else None,
            'converged': converged,
            'method': result.get('method', 'integration'),
            'max_derivative': result['integration_info'].get('max_derivative') if converged else None
        }

        # Анализ устойчивости (для фазовых портретов)
        if analyze_stability and converged:
            try:
                stability_info = finder.analyze_stability(equilibrium, {})
                result_info['stability'] = stability_info['stability']
                result_info['equilibrium_type'] = stability_info['type']
                result_info['eigenvalues'] = [complex(ev) for ev in stability_info['eigenvalues']]
            except Exception as e:
                result_info['stability_error'] = str(e)

        if not converged:
            # Если не сошлось, не рисуем асимптоты
            print(f"Warning: Equilibrium search did not converge (max derivative: {result['integration_info'].get('max_derivative', 'N/A')})")
            return result_info

        # Отрисовываем асимптоты для каждой переменной
        for i, var_name in enumerate(variable_names):
            var_config = equilibria_config.get(var_name, {})

            # Проверяем нужно ли показывать асимптоту для этой переменной
            if not var_config.get('show', False):
                continue

            # Получаем значение равновесия для этой переменной
            var_equilibrium = equilibrium[i]

            # Определяем на какой оси рисовать (левая или правая)
            # Для переменной w используем правую ось если она есть
            axis = 'right' if (var_name == 'w' and self.ax2 is not None) else 'left'

            # Получаем параметры отрисовки
            color = var_config.get('color', 'gray')
            linestyle = var_config.get('linestyle', '--')
            linewidth = var_config.get('linewidth', 1.5)
            alpha = var_config.get('alpha', 0.7)
            label = var_config.get('label', None)

            # Проверяем на nan значения (могут прийти из Excel)
            import math
            if isinstance(alpha, float) and math.isnan(alpha):
                alpha = 0.7
            if isinstance(label, float) and math.isnan(label):
                label = None

            # Рисуем горизонтальную линию
            self.add_horizontal_line(
                y=var_equilibrium,
                axis=axis,
                color=color,
                linestyle=linestyle,
                linewidth=linewidth,
                label=label,
                alpha=alpha
            )

            # Добавляем текстовую метку если указана
            if label:
                self.add_equilibrium_label(
                    y=var_equilibrium,
                    text=f"{label}={var_equilibrium:.2f}",
                    axis=axis,
                    x_position='right',
                    color=color,
                    fontsize=10
                )

        # Возвращаем информацию о равновесии
        return result_info