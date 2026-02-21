import streamlit as st
import sys
import os
import tempfile
import pandas as pd
from datetime import datetime
import base64

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.function_plotter import FunctionPlotter
from core.ode_plotter import ODEPlotter
from utils.excel_loader import ExcelConfigLoader
import params_global

st.set_page_config(
    page_title="Graph Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Профессиональный CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * {
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
    }

    /* Основной фон */
    .main {
        background: #f5f7fa;
        padding: 0;
    }

    .block-container {
        padding: 2rem 3rem !important;
        max-width: 1600px;
    }

    /* Sidebar */
    [data-testid="stSidebar"] {
        background: #ffffff;
        border-right: 1px solid #e5e7eb;
    }

    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem !important;
    }

    /* Карточки */
    .card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 2.5rem;
        margin-bottom: 2rem;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05);
    }

    /* Заголовки */
    h1 {
        color: #111827 !important;
        font-weight: 700 !important;
        font-size: 2.25rem !important;
        margin-bottom: 0.75rem !important;
        letter-spacing: -0.025em !important;
    }

    h2 {
        color: #374151 !important;
        font-weight: 600 !important;
        font-size: 1.5rem !important;
        margin-bottom: 1.5rem !important;
        letter-spacing: -0.02em !important;
    }

    h3 {
        color: #4b5563 !important;
        font-weight: 600 !important;
        font-size: 1.125rem !important;
        margin-bottom: 1rem !important;
    }

    /* Кнопки */
    .stButton>button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 8px;
        padding: 0.75rem 1.5rem;
        font-size: 0.95rem;
        font-weight: 500;
        width: 100%;
        height: auto;
        min-height: 3rem;
        transition: all 0.2s;
        letter-spacing: 0.01em;
    }

    .stButton>button:hover {
        background: #1d4ed8;
        box-shadow: 0 4px 12px rgba(37, 99, 235, 0.2);
    }

    .stButton>button[kind="primary"] {
        background: #10b981;
        font-weight: 600;
    }

    .stButton>button[kind="primary"]:hover {
        background: #059669;
        box-shadow: 0 4px 12px rgba(16, 185, 129, 0.25);
    }

    /* Поля ввода */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stTextArea textarea {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        padding: 0.75rem;
        font-size: 0.95rem;
        background: white;
        transition: all 0.2s;
    }

    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus,
    .stTextArea textarea:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 3px rgba(37, 99, 235, 0.1);
    }

    /* Labels */
    .stTextInput label,
    .stNumberInput label,
    .stSelectbox label,
    .stTextArea label {
        color: #374151 !important;
        font-weight: 500 !important;
        font-size: 0.875rem !important;
        margin-bottom: 0.5rem !important;
    }

    /* Selectbox */
    .stSelectbox>div>div {
        border-radius: 8px;
        border: 1px solid #d1d5db;
        background: white;
    }

    /* Slider */
    .stSlider {
        padding: 0.5rem 0;
    }

    /* Radio buttons */
    .stRadio>div {
        gap: 0.75rem;
    }

    .stRadio>div>label {
        background: #f9fafb;
        padding: 0.75rem 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        transition: all 0.2s;
        cursor: pointer;
        font-weight: 500;
        color: #374151;
    }

    .stRadio>div>label:hover {
        background: #f3f4f6;
        border-color: #d1d5db;
    }

    .stRadio>div>label[data-checked="true"] {
        background: #eff6ff;
        border-color: #2563eb;
        color: #2563eb;
    }

    /* Tabs */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.5rem;
        border-bottom: 1px solid #e5e7eb;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 8px 8px 0 0;
        padding: 0.75rem 1.5rem;
        font-weight: 500;
        color: #6b7280;
        border-bottom: 2px solid transparent;
    }

    .stTabs [data-baseweb="tab"]:hover {
        color: #374151;
        background: #f9fafb;
    }

    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #2563eb;
        border-bottom-color: #2563eb;
        background: transparent;
    }

    /* Download button */
    .stDownloadButton>button {
        background: #10b981;
        color: white;
        border-radius: 8px;
        font-weight: 500;
        padding: 0.75rem 1.5rem;
    }

    .stDownloadButton>button:hover {
        background: #059669;
    }

    /* Success/Error messages */
    .stSuccess {
        background: #ecfdf5;
        border: 1px solid #10b981;
        border-radius: 8px;
        padding: 1rem;
        color: #065f46;
    }

    .stError {
        background: #fef2f2;
        border: 1px solid #ef4444;
        border-radius: 8px;
        padding: 1rem;
        color: #991b1b;
    }

    .stInfo {
        background: #eff6ff;
        border: 1px solid #3b82f6;
        border-radius: 8px;
        padding: 1rem;
        color: #1e40af;
    }

    /* Галерея */
    .gallery-card {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 1.25rem;
        transition: all 0.2s;
        cursor: pointer;
        margin-bottom: 1.5rem;
    }

    .gallery-card:hover {
        border-color: #2563eb;
        box-shadow: 0 4px 16px rgba(0, 0, 0, 0.08);
        transform: translateY(-2px);
    }

    /* Предпросмотр графика */
    .graph-preview {
        background: white;
        border: 1px solid #e5e7eb;
        border-radius: 12px;
        padding: 2rem;
        margin: 2rem 0;
    }

    /* Expander */
    .streamlit-expanderHeader {
        background: #f9fafb;
        border-radius: 8px;
        font-weight: 500;
        color: #374151;
    }

    /* Progress bar */
    .stProgress>div>div {
        background: #2563eb;
    }

    /* Dataframe */
    .stDataFrame {
        border: 1px solid #e5e7eb;
        border-radius: 8px;
    }

    /* Caption */
    .caption {
        color: #6b7280;
        font-size: 0.875rem;
    }

    /* Удалить стрелки у number input */
    input[type=number]::-webkit-inner-spin-button,
    input[type=number]::-webkit-outer-spin-button {
        opacity: 1;
    }
</style>
""", unsafe_allow_html=True)

# fix_latex() REMOVED - parse_latex() from sympy handles LaTeX natively
# No need to escape backslashes - just pass \sin, \exp, \alpha, etc. as-is

# Расширенная цветовая палитра для iPad
COLOR_OPTIONS = {
    "Красный": "red",
    "Синий": "blue",
    "Зеленый": "green",
    "Оранжевый": "orange",
    "Фиолетовый": "purple",
    "Голубой": "cyan",
    "Розовый": "magenta",
    "Желтый": "yellow",
    "Черный": "black",
    "Серый": "gray",
    "Коричневый": "brown",
    "Лайм": "lime",
    "Темно-синий": "navy",
    "Бордовый": "maroon",
    "Оливковый": "olive"
}

# Session state
if 'graph_history' not in st.session_state:
    st.session_state.graph_history = []
if 'current_graph' not in st.session_state:
    st.session_state.current_graph = None

# Header
st.title("Graph Builder")
st.caption("Построение математических графиков для курсовой работы")
st.markdown("---")

# Sidebar
with st.sidebar:
    st.subheader("Режим работы")
    mode = st.radio(
        "Выберите режим работы",
        ["Построить график", "Загрузить Excel", "Мои графики"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    if st.session_state.graph_history:
        st.success(f"Построено графиков: {len(st.session_state.graph_history)}")
        if st.button("Очистить всё", width="stretch"):
            st.session_state.graph_history = []
            st.session_state.current_graph = None

    st.markdown("---")
    st.caption("Для iPad Pro 11 дюймов")

# ========== МОИ ГРАФИКИ ==========
if mode == "Мои графики":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Галерея графиков")

    if not st.session_state.graph_history:
        st.info("Графики еще не построены. Перейдите в режим 'Построить график'")
    else:
        for i in range(0, len(st.session_state.graph_history), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(st.session_state.graph_history):
                    graph = st.session_state.graph_history[i + j]
                    with col:
                        st.markdown("<div class='gallery-card'>", unsafe_allow_html=True)
                        st.markdown(f"**{graph['name']}**")
                        st.caption(f"Время: {graph['timestamp']}")

                        if 'svg_data' in graph:
                            svg_b64 = base64.b64encode(graph['svg_data']).decode()
                            st.markdown(
                                f'<img src="data:image/svg+xml;base64,{svg_b64}" style="width: 100%; border-radius: 8px;">',
                                unsafe_allow_html=True
                            )

                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.download_button(
                                    "Скачать",
                                    graph['svg_data'],
                                    file_name=f"{graph['name']}.svg",
                                    mime="image/svg+xml",
                                    width="stretch",
                                    key=f"dl_{i}_{j}"
                                )
                            with col_b:
                                if st.button("Удалить", width="stretch", key=f"del_{i}_{j}"):
                                    st.session_state.graph_history.pop(i+j)

                        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ========== EXCEL ==========
elif mode == "Загрузить Excel":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Загрузка Excel файла")

    st.info("Загрузите таблицу с конфигурациями графиков (.xlsx или .xls)")

    uploaded_file = st.file_uploader(
        "Выберите файл",
        type=['xlsx', 'xls'],
        label_visibility="collapsed"
    )

    if uploaded_file:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            loader = ExcelConfigLoader(tmp_path)
            df = loader.load_table()
            loader.validate_table()

            st.success(f"Загружено строк: {len(df)}")

            with st.expander("Предпросмотр таблицы", expanded=True):
                st.dataframe(df, width="stretch", height=300)

            if st.button("Построить все графики", type="primary", width="stretch"):
                grouped_rows = loader.get_rows_grouped_by_output()
                total_graphs = len(grouped_rows)

                progress = st.progress(0)
                success_count = 0
                error_count = 0

                for idx, (output_file, rows) in enumerate(grouped_rows.items(), 1):
                    progress.progress(idx / total_graphs)

                    try:
                        # Определяем тип графика из первой строки
                        first_row = rows[0]
                        graph_type = first_row.get('graph_type', first_row.get('type', 'ode_time'))

                        # Создаем плоттер
                        if graph_type == 'function':
                            plotter = FunctionPlotter(vars(params_global))
                        else:
                            plotter = ODEPlotter(vars(params_global))

                            # Проверяем, нужны ли две оси Y
                            dual_y = first_row.get('dual_y_axis') or first_row.get('dual_y') or first_row.get('two_axes')
                            if dual_y:
                                # Преобразуем в bool
                                if isinstance(dual_y, str):
                                    dual_y = dual_y.lower() in ('true', 'yes', '1', 'да')
                                else:
                                    dual_y = bool(dual_y)

                                if dual_y:
                                    plotter.enable_dual_y_axis()

                        # Определяем цветовую палитру для случая, если цвета не указаны
                        default_colors = ['#FF0000', '#00FF00', '#0000FF', '#FF00FF', '#00FFFF',
                                        '#FFA500', '#800080', '#008000', '#000080', '#FF1493']

                        # Строим каждую кривую
                        for curve_idx, row in enumerate(rows):
                            if graph_type == 'function':
                                formula = row.get('formula', row.get('equation_1', 'x'))
                                # Автоматически исправляем LaTeX
                                # formula = fix_latex(formula)  # REMOVED: parse_latex handles LaTeX natively

                                x_min = row.get('x_min', row.get('xlim_min', -10))
                                x_max = row.get('x_max', row.get('xlim_max', 10))

                                # Получаем цвет из разных возможных колонок
                                color = row.get('color') or row.get('Color') or row.get('col') or default_colors[curve_idx % len(default_colors)]
                                linewidth = row.get('linewidth', 2.0)

                                # Получаем linestyle
                                linestyle_raw = row.get('linestyle') or row.get('line_style') or row.get('ls') or '-'
                                linestyle_map = {
                                    'solid': '-', '-': '-',
                                    'dashed': '--', 'dash': '--', '--': '--',
                                    'dotted': ':', 'dot': ':', ':': ':',
                                    'dashdot': '-.', 'dash-dot': '-.', '-.': '-.'
                                }
                                actual_linestyle = linestyle_map.get(str(linestyle_raw).lower().strip(), '-')

                                plotter.add_curve_from_latex(
                                    formula, {}, [x_min, x_max],
                                    {"color": color, "linewidth": linewidth, "linestyle": actual_linestyle}
                                )

                            elif graph_type == 'ode_time':
                                # Получаем уравнения
                                eq1 = row.get('equation_1', 'x')
                                eq2 = row.get('equation_2', 'y')
                                # Автоматически исправляем LaTeX
                                # eq1 = fix_latex(eq1)  # REMOVED
                                # eq2 = fix_latex(eq2)  # REMOVED
                                equations = [eq1, eq2]

                                var_names = ['s', 'w']

                                # Начальные условия
                                # s0 -> начальное условие для s
                                # w0 -> начальное условие для w
                                ic_s = row.get('ic_1', row.get('s0', 1.0))
                                ic_w = row.get('ic_2', row.get('w0', 0.0))
                                ics = [ic_s, ic_w]

                                # Время интегрирования
                                t_start = row.get('t_start', 0)
                                t_end = row.get('t_end', 100)  # По умолчанию 100

                                # Собираем параметры из колонок Excel
                                # a, b, h, alpha, betta, c - это параметры уравнений
                                params = {}
                                param_cols = ['a', 'b', 'h', 'alpha', 'betta', 'beta', 'c']

                                for param_name in param_cols:
                                    if param_name in row and row[param_name] is not None:
                                        params[param_name] = row[param_name]

                                # Получаем цвет из Excel (пробуем разные варианты названия колонки)
                                color_raw = row.get('color') or row.get('Color') or row.get('col') or None

                                # Если цвет не найден, используем цвет из палитры по индексу
                                if not color_raw or str(color_raw).strip() == '':
                                    actual_color = default_colors[curve_idx % len(default_colors)]
                                else:
                                    # Маппинг цветов из текста в matplotlib colors
                                    color_map = {
                                        'cyan': '#00FFFF',
                                        'black': '#000000',
                                        'green': '#00FF00',
                                        'greer': '#00FF00',
                                        'blue': '#0000FF',
                                        'red': '#FF0000',
                                        'orange': '#FFA500',
                                        'purple': '#800080',
                                        'yellow': '#FFFF00',
                                        'pink': '#FF1493',
                                        'brown': '#8B4513',
                                        'gray': '#808080',
                                        'grey': '#808080'
                                    }
                                    actual_color = color_map.get(str(color_raw).lower().strip(), str(color_raw))

                                # Получаем linestyle из Excel
                                linestyle_raw = row.get('linestyle') or row.get('line_style') or row.get('ls') or '-'

                                # Маппинг стилей линий
                                linestyle_map = {
                                    'solid': '-',
                                    '-': '-',
                                    'dashed': '--',
                                    'dash': '--',
                                    '--': '--',
                                    'dotted': ':',
                                    'dot': ':',
                                    ':': ':',
                                    'dashdot': '-.',
                                    'dash-dot': '-.',
                                    '-.': '-.'
                                }
                                actual_linestyle = linestyle_map.get(str(linestyle_raw).lower().strip(), '-')

                                # Проверяем, используется ли dual_y_axis
                                use_dual_y = first_row.get('dual_y_axis') or first_row.get('dual_y') or first_row.get('two_axes')
                                if isinstance(use_dual_y, str):
                                    use_dual_y = use_dual_y.lower() in ('true', 'yes', '1', 'да')
                                else:
                                    use_dual_y = bool(use_dual_y) if use_dual_y else False

                                if use_dual_y:
                                    # Две оси: s на левой, w на правой
                                    styles = [
                                        {"color": actual_color, "linewidth": 2.0, "linestyle": actual_linestyle},  # s на левой оси
                                        {"color": 'red', "linewidth": 1.5, "linestyle": ':', "use_right_axis": True}  # w на правой оси
                                    ]
                                else:
                                    # Одна ось: строим только s, w не строим
                                    styles = [
                                        {"color": actual_color, "linewidth": 2.0, "linestyle": actual_linestyle},  # для s
                                        None  # для w - НЕ строим
                                    ]

                                plotter.solve_and_plot_time(
                                    equations, var_names, ics, params,
                                    [t_start, t_end], styles
                                )

                        # Настраиваем оси
                        xlabel = first_row.get('xlabel', 't')
                        ylabel = first_row.get('ylabel', 'value')

                        # Проверяем dual_y_axis для настройки осей
                        use_dual_y = first_row.get('dual_y_axis') or first_row.get('dual_y') or first_row.get('two_axes')
                        if isinstance(use_dual_y, str):
                            use_dual_y = use_dual_y.lower() in ('true', 'yes', '1', 'да')
                        else:
                            use_dual_y = bool(use_dual_y) if use_dual_y else False

                        if use_dual_y and graph_type == 'ode_time':
                            ylabel_right = first_row.get('ylabel_right', 'w')
                            plotter.set_axes(
                                xlabel=xlabel,
                                ylabel=ylabel if ylabel != 'value' else 's',
                                ylabel_right=ylabel_right,
                                dual_y_axis=True,
                                grid=True
                            )
                        else:
                            plotter.set_axes(xlabel=xlabel, ylabel=ylabel, grid=True)

                        # Сохраняем в SVG
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                            plotter.save(tmp.name)
                            with open(tmp.name, 'rb') as f:
                                svg_data = f.read()

                            st.session_state.graph_history.append({
                                'name': output_file,
                                'timestamp': datetime.now().strftime('%H:%M:%S'),
                                'type': graph_type,
                                'svg_data': svg_data
                            })
                            os.unlink(tmp.name)

                        success_count += 1

                    except Exception as e:
                        error_count += 1
                        st.error(f"Ошибка для {output_file}: {str(e)}")

                progress.empty()
                if success_count > 0:
                    st.success(f"Построено графиков: {success_count}")
                if error_count > 0:
                    st.warning(f"Ошибок: {error_count}")

            os.unlink(tmp_path)

        except Exception as e:
            st.error(f"Ошибка: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# ========== ПОСТРОИТЬ ГРАФИК ==========
else:
    tab1, tab2, tab3 = st.tabs(["Функция", "ОДУ", "Фазовый портрет"])

    # ========== ФУНКЦИЯ ==========
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("График функции")

        col1, col2 = st.columns([3, 1])

        with col1:
            formula = st.text_input(
                "Формула LaTeX",
                value="x^2",
                placeholder="x^2 + \\\\sin(x)",
                help="Используйте двойной слеш: \\\\sin, \\\\cos, \\\\exp"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                x_min = st.number_input("x min", value=-10.0, step=1.0)
            with col_b:
                x_max = st.number_input("x max", value=10.0, step=1.0)

        with col2:
            st.markdown("**Стиль**")
            color_name = st.selectbox("Цвет", list(COLOR_OPTIONS.keys()), index=1)  # Синий по умолчанию
            color = COLOR_OPTIONS[color_name]
            linewidth = st.slider("Толщина", 0.5, 4.0, 2.0, step=0.1)
            alpha = st.slider("Прозрачность", 0.0, 1.0, 1.0, step=0.05, help="0 = полностью прозрачный, 1 = непрозрачный")
            linestyle_func = st.selectbox("Тип линии",
                                         ["Сплошная", "Пунктир", "Точки", "Штрих-пунктир"],
                                         key="linestyle_func")

            st.markdown("**Оси графика**")
            show_top_spine = st.checkbox("Верхняя ось", value=False, key="show_top_func")
            show_right_spine = st.checkbox("Правая ось", value=False, key="show_right_func")

        col1, col2, col3 = st.columns(3)
        with col1:
            xlabel = st.text_input("Ось X", value="x")
        with col2:
            ylabel = st.text_input("Ось Y", value="f(x)")
        with col3:
            filename = st.text_input("Имя файла", value="function")

        if st.button("Построить", type="primary", width="stretch"):
            try:
                with st.spinner("Построение графика..."):
                    # Автоматически исправляем LaTeX
                    formula_fixed = formula  # parse_latex handles LaTeX natively

                    # Маппинг стилей линий
                    linestyle_mapping = {
                        "Сплошная": "-",
                        "Пунктир": "--",
                        "Точки": ":",
                        "Штрих-пунктир": "-."
                    }
                    ls = linestyle_mapping.get(linestyle_func, "-")

                    plotter = FunctionPlotter(vars(params_global))
                    plotter.add_curve_from_latex(
                        formula_fixed, {}, [x_min, x_max],
                        {"color": color, "linewidth": linewidth, "linestyle": ls, "alpha": alpha}
                    )

                    # Настройка видимости осей
                    spines_config = {
                        'top': show_top_spine,
                        'right': show_right_spine,
                        'bottom': True,  # Нижняя ось всегда видима
                        'left': True      # Левая ось всегда видима
                    }

                    plotter.set_axes(
                        xlim=[x_min, x_max],
                        xlabel=xlabel,
                        ylabel=ylabel,
                        grid=True,
                        spines=spines_config
                    )

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                        plotter.save(tmp.name)
                        with open(tmp.name, 'rb') as f:
                            svg_data = f.read()

                        st.session_state.graph_history.append({
                            'name': filename,
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'type': 'function',
                            'svg_data': svg_data
                        })
                        st.session_state.current_graph = svg_data
                        os.unlink(tmp.name)

                st.success("График успешно построен")

            except Exception as e:
                st.error(f"Ошибка: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ========== ОДУ ==========
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Система ОДУ")

        col1, col2 = st.columns([2, 1])

        with col1:
            num_vars = st.number_input("Количество переменных", 2, 4, 2, 1)

            equations = []
            var_names = []
            ics = []
            colors_list = []

            for i in range(num_vars):
                st.markdown(f"**Переменная {i+1}**")
                col_a, col_b, col_c, col_d = st.columns([1, 2, 1, 1])

                with col_a:
                    var = st.text_input("Имя", value=chr(120+i), key=f"var_{i}", label_visibility="collapsed")
                    var_names.append(var)
                with col_b:
                    eq = st.text_input("Уравнение", value="-x" if i==0 else "x-y", key=f"eq_{i}", label_visibility="collapsed")
                    equations.append(eq)
                with col_c:
                    ic = st.number_input("Нач. усл.", value=float(i+1), key=f"ic_{i}", label_visibility="collapsed")
                    ics.append(ic)
                with col_d:
                    c_name = st.selectbox("Цвет", list(COLOR_OPTIONS.keys()), index=min(i, len(COLOR_OPTIONS)-1), key=f"c_{i}", label_visibility="collapsed")
                    colors_list.append(COLOR_OPTIONS[c_name])

        with col2:
            st.markdown("**Время**")
            t_start = st.number_input("Начало", value=0.0)
            t_end = st.number_input("Конец", value=10.0)

            st.markdown("**Оси**")
            use_dual_y_manual = st.checkbox("Две оси Y", value=False, key="dual_y_manual",
                                           help="Первая переменная на левой оси, вторая на правой")
            xlabel_ode = st.text_input("X", value="t", key="xlabel_ode")
            ylabel_ode = st.text_input("Y левая", value="значение", key="ylabel_ode")
            if use_dual_y_manual:
                ylabel_right_ode = st.text_input("Y правая", value="значение 2", key="ylabel_right_ode")
            filename_ode = st.text_input("Файл", value="ode", key="file_ode")

        if st.button("Построить", type="primary", width="stretch", key="build_ode"):
            try:
                with st.spinner("Решение системы ОДУ..."):
                    plotter = ODEPlotter(vars(params_global))

                    # Если используются две оси, включаем dual_y_axis
                    if use_dual_y_manual:
                        plotter.enable_dual_y_axis()

                    # Автоматически исправляем LaTeX в уравнениях
                    equations_fixed = equations  # parse_latex handles LaTeX natively

                    # Создаем стили с учетом dual_y_axis
                    if use_dual_y_manual and num_vars >= 2:
                        # Первая переменная на левой оси, вторая на правой
                        styles = [
                            {"color": colors_list[0], "linewidth": 2.0},
                            {"color": colors_list[1], "linewidth": 2.0, "use_right_axis": True}
                        ]
                        # Остальные переменные на левой оси
                        for i in range(2, num_vars):
                            styles.append({"color": colors_list[i], "linewidth": 1.5, "linestyle": "--"})
                    else:
                        styles = [{"color": colors_list[i], "linewidth": 2.0} for i in range(num_vars)]

                    plotter.solve_and_plot_time(
                        equations_fixed, var_names, ics, {},
                        [t_start, t_end], styles
                    )

                    # Настраиваем оси с учетом dual_y_axis
                    if use_dual_y_manual and num_vars >= 2:
                        plotter.set_axes(
                            xlabel=xlabel_ode,
                            ylabel=ylabel_ode,
                            ylabel_right=ylabel_right_ode,
                            dual_y_axis=True,
                            grid=True
                        )
                    else:
                        plotter.set_axes(xlabel=xlabel_ode, ylabel=ylabel_ode, grid=True)

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                        plotter.save(tmp.name)
                        with open(tmp.name, 'rb') as f:
                            svg_data = f.read()

                        st.session_state.graph_history.append({
                            'name': filename_ode,
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'type': 'ode',
                            'svg_data': svg_data
                        })
                        st.session_state.current_graph = svg_data
                        os.unlink(tmp.name)

                st.success("ОДУ успешно решена")

            except Exception as e:
                st.error(f"Ошибка: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

    # ========== ФАЗОВЫЙ ПОРТРЕТ ==========
    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Фазовый портрет")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**Система уравнений**")

            col_a, col_b = st.columns(2)
            with col_a:
                var1 = st.text_input("Переменная 1", value="x")
                eq1 = st.text_input(f"d{var1}/dt", value="y", help="Используйте двойной слеш: \\\\sin, \\\\cos, \\\\exp")
                ic1 = st.number_input(f"{var1}(0)", value=1.5)

            with col_b:
                var2 = st.text_input("Переменная 2", value="y")
                eq2 = st.text_input(f"d{var2}/dt", value=r"-\sin(x)", help="Используйте одинарный слеш: \\sin, \\cos, \\exp")
                ic2 = st.number_input(f"{var2}(0)", value=0.0)

        with col2:
            st.markdown("**Настройки**")
            t_end_pp = st.number_input("Время", value=50.0, step=5.0)
            color_pp_name = st.selectbox("Цвет траектории", list(COLOR_OPTIONS.keys()), index=1)
            color_pp = COLOR_OPTIONS[color_pp_name]
            linewidth_pp = st.slider("Толщина линии", 0.5, 4.0, 2.0, step=0.1)
            alpha_pp = st.slider("Прозрачность", 0.0, 1.0, 1.0, step=0.05)
            show_vector = st.checkbox("Векторное поле", value=True)

            if show_vector:
                density = st.slider("Плотность поля", 5, 30, 15)

            st.markdown("**Оси графика**")
            show_top_spine_pp = st.checkbox("Верхняя ось", value=False, key="show_top_pp")
            show_right_spine_pp = st.checkbox("Правая ось", value=False, key="show_right_pp")

            xlabel_pp = st.text_input("Ось X", value="x", key="xlabel_pp")
            ylabel_pp = st.text_input("Ось Y", value="y", key="ylabel_pp")
            filename_pp = st.text_input("Файл", value="phase", key="file_pp")

        if st.button("Построить", type="primary", width="stretch", key="build_phase"):
            try:
                with st.spinner("Построение фазового портрета..."):
                    # parse_latex handles LaTeX natively - no escaping needed
                    eq1_fixed = eq1
                    eq2_fixed = eq2

                    plotter = ODEPlotter(vars(params_global))

                    if show_vector:
                        plotter.add_vector_field(
                            [eq1_fixed, eq2_fixed], [var1, var2], {}, [0, 1],
                            {"density": density, "color": "gray", "alpha": 0.4}
                        )

                    plotter.solve_and_plot_phase(
                        [eq1_fixed, eq2_fixed], [var1, var2], [ic1, ic2], {},
                        [0, t_end_pp], [0, 1],
                        {"color": color_pp, "linewidth": linewidth_pp, "alpha": alpha_pp}
                    )

                    # Настройка видимости осей
                    spines_config_pp = {
                        'top': show_top_spine_pp,
                        'right': show_right_spine_pp,
                        'bottom': True,
                        'left': True
                    }

                    plotter.set_axes(
                        xlabel=xlabel_pp,
                        ylabel=ylabel_pp,
                        grid=True,
                        spines=spines_config_pp
                    )

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                        plotter.save(tmp.name)
                        with open(tmp.name, 'rb') as f:
                            svg_data = f.read()

                        st.session_state.graph_history.append({
                            'name': filename_pp,
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'type': 'phase',
                            'svg_data': svg_data
                        })
                        st.session_state.current_graph = svg_data
                        os.unlink(tmp.name)

                st.success("Фазовый портрет успешно построен")

            except Exception as e:
                st.error(f"Ошибка: {str(e)}")

        st.markdown("</div>", unsafe_allow_html=True)

# ========== ПРЕДПРОСМОТР ==========
if st.session_state.current_graph is not None and mode == "Построить график":
    st.markdown("<div class='card graph-preview'>", unsafe_allow_html=True)
    st.subheader("Предпросмотр результата")

    col1, col2 = st.columns([4, 1])

    with col1:
        svg_b64 = base64.b64encode(st.session_state.current_graph).decode()
        st.markdown(
            f'<img src="data:image/svg+xml;base64,{svg_b64}" style="width: 100%; border-radius: 8px;">',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("**Действия**")

        st.download_button(
            "Скачать SVG",
            st.session_state.current_graph,
            file_name=f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
            mime="image/svg+xml",
            width="stretch"
        )

        if st.button("Построить новый", width="stretch"):
            st.session_state.current_graph = None

    st.markdown("</div>", unsafe_allow_html=True)

# Footer
st.markdown("---")
import subprocess
import os

# Получаем информацию о последнем коммите Git
try:
    git_hash = subprocess.check_output(['git', 'rev-parse', '--short', 'HEAD'],
                                       cwd=os.path.dirname(__file__)).decode('utf-8').strip()
    git_date = subprocess.check_output(['git', 'log', '-1', '--format=%cd', '--date=format:%Y-%m-%d %H:%M'],
                                       cwd=os.path.dirname(__file__)).decode('utf-8').strip()
    version_info = f"v{git_hash} ({git_date})"
except:
    version_info = "unknown"

col1, col2, col3 = st.columns([2, 1, 2])
with col1:
    st.caption(f"📊 Графиков построено: {len(st.session_state.graph_history)}")
with col2:
    st.caption(f"🔄 {version_info}")
with col3:
    st.caption("Для iPad Pro 11\"")
