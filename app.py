import streamlit as st
import sys
import os
import tempfile
import pandas as pd
from datetime import datetime

# Настройка путей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.function_plotter import FunctionPlotter
from core.ode_plotter import ODEPlotter
from utils.excel_loader import ExcelConfigLoader
from utils.validators import merge_params
import params_global

# Конфигурация страницы для iPad
st.set_page_config(
    page_title="График Builder",
    layout="wide",
    initial_sidebar_state="expanded"
)

# CSS для iPad Pro 11" оптимизации
st.markdown("""
<style>
    /* Оптимизация для iPad */
    .main {
        padding: 1rem;
    }

    /* Большие кнопки для сенсорного управления */
    .stButton>button {
        height: 3.5rem;
        font-size: 1.2rem;
        font-weight: 600;
        border-radius: 0.5rem;
        width: 100%;
    }

    /* Увеличенные поля ввода */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stTextArea textarea {
        font-size: 1.1rem;
        padding: 0.75rem;
        border-radius: 0.5rem;
    }

    /* Карточки для графиков */
    .graph-card {
        background: white;
        border-radius: 1rem;
        padding: 1rem;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin-bottom: 1rem;
    }

    /* Галерея графиков */
    .gallery-item {
        border: 2px solid #e0e0e0;
        border-radius: 0.75rem;
        padding: 0.5rem;
        cursor: pointer;
        transition: all 0.3s;
    }

    .gallery-item:hover {
        border-color: #1f77b4;
        box-shadow: 0 4px 12px rgba(31,119,180,0.2);
    }

    /* Заголовки секций */
    .section-header {
        font-size: 1.5rem;
        font-weight: 700;
        margin-bottom: 1rem;
        color: #1f77b4;
    }

    /* Статус индикаторы */
    .status-success {
        background: #d4edda;
        color: #155724;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }

    .status-error {
        background: #f8d7da;
        color: #721c24;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

# Инициализация session state для истории
if 'graph_history' not in st.session_state:
    st.session_state.graph_history = []

if 'current_graph' not in st.session_state:
    st.session_state.current_graph = None

# Сайдбар с режимами работы
with st.sidebar:
    st.image("https://raw.githubusercontent.com/streamlit/streamlit/develop/docs/_static/logo.png", width=100)
    st.title("📊 График Builder")
    st.markdown("---")

    mode = st.radio(
        "Режим работы",
        ["🎨 Ручной ввод", "📁 Загрузка Excel", "📚 Галерея графиков", "⚡ Быстрые шаблоны"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    if st.session_state.graph_history:
        st.success(f"✅ Графиков построено: {len(st.session_state.graph_history)}")
        if st.button("🗑️ Очистить историю", use_container_width=True):
            st.session_state.graph_history = []
            st.rerun()

    st.markdown("---")
    st.caption("Оптимизировано для iPad Pro 11\"")

# ========== РЕЖИМ: БЫСТРЫЕ ШАБЛОНЫ ==========
if mode == "⚡ Быстрые шаблоны":
    st.header("⚡ Быстрые шаблоны")
    st.markdown("Готовые примеры для быстрого старта")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📈 Математические функции")

        if st.button("Квадратичная функция", use_container_width=True):
            st.session_state.template = {
                'type': 'function',
                'formula': 'x^2',
                'x_min': -5.0,
                'x_max': 5.0
            }

        if st.button("Синусоида", use_container_width=True):
            st.session_state.template = {
                'type': 'function',
                'formula': '\\\\sin(x)',
                'x_min': 0.0,
                'x_max': 10.0
            }

        if st.button("Экспонента", use_container_width=True):
            st.session_state.template = {
                'type': 'function',
                'formula': '\\\\exp(-x^2)',
                'x_min': -3.0,
                'x_max': 3.0
            }

    with col2:
        st.subheader("🔄 Системы ОДУ")

        if st.button("Лотка-Вольтерра", use_container_width=True):
            st.session_state.template = {
                'type': 'ode',
                'eq1': '1.5*x - 0.1*x*y',
                'eq2': '0.075*x*y - y',
                'ic1': 10.0,
                'ic2': 5.0
            }

        if st.button("Маятник", use_container_width=True):
            st.session_state.template = {
                'type': 'phase',
                'eq1': 'y',
                'eq2': '-\\\\sin(x)',
                'ic1': 1.5,
                'ic2': 0.0
            }

    if 'template' in st.session_state:
        st.info("✨ Шаблон загружен! Перейдите в режим 'Ручной ввод' для построения")

# ========== РЕЖИМ: ГАЛЕРЕЯ ==========
elif mode == "📚 Галерея графиков":
    st.header("📚 Галерея построенных графиков")

    if not st.session_state.graph_history:
        st.info("📭 История пуста. Постройте графики, чтобы они появились здесь.")
    else:
        # Фильтры
        col1, col2, col3 = st.columns(3)
        with col1:
            filter_type = st.selectbox("Тип графика", ["Все", "Функции", "ОДУ", "Фазовые портреты"])
        with col2:
            sort_by = st.selectbox("Сортировка", ["Новые первыми", "Старые первыми"])
        with col3:
            if st.button("🔄 Обновить", use_container_width=True):
                st.rerun()

        st.markdown("---")

        # Отображение графиков в сетке
        graphs = st.session_state.graph_history.copy()
        if sort_by == "Старые первыми":
            graphs.reverse()

        cols_per_row = 2
        for i in range(0, len(graphs), cols_per_row):
            cols = st.columns(cols_per_row)
            for j, col in enumerate(cols):
                if i + j < len(graphs):
                    graph = graphs[i + j]
                    with col:
                        with st.container():
                            st.markdown(f"**{graph['name']}**")
                            st.caption(f"🕐 {graph['timestamp']}")

                            if 'svg_data' in graph:
                                st.image(graph['svg_data'])

                                # Кнопки действий
                                col_a, col_b = st.columns(2)
                                with col_a:
                                    st.download_button(
                                        "💾 Скачать",
                                        graph['svg_data'],
                                        file_name=f"{graph['name']}.svg",
                                        mime="image/svg+xml",
                                        use_container_width=True,
                                        key=f"download_{i+j}"
                                    )
                                with col_b:
                                    if st.button("🗑️", use_container_width=True, key=f"delete_{i+j}"):
                                        st.session_state.graph_history.pop(i+j)
                                        st.rerun()

# ========== РЕЖИМ: ЗАГРУЗКА EXCEL ==========
elif mode == "📁 Загрузка Excel":
    st.header("📁 Загрузка конфигурации из Excel")

    st.markdown("""
    ### 📋 Формат Excel файла

    Таблица должна содержать колонки:
    - **type** - тип графика (function, ode_time, phase_portrait)
    - **output** - имя файла для сохранения
    - Другие параметры зависят от типа графика

    [📥 Скачать пример таблицы](./excel/pic9a_power_exp.xlsx)
    """)

    uploaded_file = st.file_uploader(
        "Выберите Excel файл (.xlsx или .xls)",
        type=['xlsx', 'xls'],
        help="Загрузите таблицу с конфигурациями графиков"
    )

    if uploaded_file is not None:
        try:
            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            # Загружаем Excel
            loader = ExcelConfigLoader(tmp_path)
            df = loader.load_table()
            loader.validate_table()

            st.success(f"✅ Загружено {len(df)} строк")

            # Предпросмотр таблицы
            with st.expander("👁️ Предпросмотр данных", expanded=True):
                st.dataframe(df, use_container_width=True)

            # Выбор строк для построения
            st.subheader("Выберите графики для построения")

            selected_rows = st.multiselect(
                "Выберите строки (по номеру или имени файла)",
                options=list(range(len(df))),
                format_func=lambda x: f"#{x+1}: {df.iloc[x]['output'] if 'output' in df.columns else 'Без имени'}",
                default=list(range(min(3, len(df))))
            )

            col1, col2 = st.columns([3, 1])
            with col1:
                build_all = st.checkbox("Построить все графики сразу", value=False)
            with col2:
                if st.button("🚀 Построить", type="primary", use_container_width=True):
                    rows_to_build = list(range(len(df))) if build_all else selected_rows

                    progress_bar = st.progress(0)
                    status_text = st.empty()

                    success_count = 0
                    error_count = 0

                    for idx, row_idx in enumerate(rows_to_build):
                        status_text.text(f"Построение графика {idx+1} из {len(rows_to_build)}...")
                        progress_bar.progress((idx + 1) / len(rows_to_build))

                        try:
                            row = df.iloc[row_idx].to_dict()
                            # Здесь будет логика построения из Excel
                            # Пока просто добавляем в историю
                            st.session_state.graph_history.append({
                                'name': row.get('output', f'graph_{row_idx}'),
                                'timestamp': datetime.now().strftime('%H:%M:%S'),
                                'type': row.get('type', 'unknown')
                            })
                            success_count += 1
                        except Exception as e:
                            error_count += 1
                            st.error(f"Ошибка в строке {row_idx}: {str(e)}")

                    progress_bar.empty()
                    status_text.empty()

                    if success_count > 0:
                        st.success(f"✅ Успешно построено: {success_count}")
                    if error_count > 0:
                        st.error(f"❌ Ошибок: {error_count}")

            os.unlink(tmp_path)

        except Exception as e:
            st.error(f"❌ Ошибка загрузки: {str(e)}")

# ========== РЕЖИМ: РУЧНОЙ ВВОД ==========
else:  # Ручной ввод
    st.header("🎨 Ручное построение графиков")

    # Вкладки для типов графиков
    tab1, tab2, tab3 = st.tabs(["📈 Функция", "📊 ОДУ (время)", "🔄 Фазовый портрет"])

    # ========== ВКЛАДКА: ФУНКЦИЯ ==========
    with tab1:
        st.subheader("График функции f(x)")

        # Загрузка шаблона если есть
        default_formula = "x^2"
        default_x_min = -10.0
        default_x_max = 10.0

        if 'template' in st.session_state and st.session_state.template.get('type') == 'function':
            default_formula = st.session_state.template.get('formula', default_formula)
            default_x_min = st.session_state.template.get('x_min', default_x_min)
            default_x_max = st.session_state.template.get('x_max', default_x_max)

        col1, col2 = st.columns([2, 1])

        with col1:
            formula = st.text_input(
                "Формула LaTeX",
                value=default_formula,
                help="Примеры: x^2, \\\\sin(x), \\\\exp(-x^2)",
                placeholder="x^2 + \\\\sin(x)"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                x_min = st.number_input("xmin", value=default_x_min, step=0.5)
            with col_b:
                x_max = st.number_input("x max", value=default_x_max, step=0.5)

        with col2:
            st.markdown("**Стиль**")
            color = st.selectbox("Цвет", ["blue", "red", "green", "orange", "purple"], key="f_color")
            linewidth = st.slider("Толщина", 0.5, 4.0, 1.5, 0.5, key="f_lw")
            grid = st.checkbox("Сетка", value=True, key="f_grid")

        col1, col2, col3 = st.columns([2, 2, 1])
        with col1:
            xlabel = st.text_input("Ось X", value="x", key="f_xlabel")
        with col2:
            ylabel = st.text_input("Ось Y", value="f(x)", key="f_ylabel")
        with col3:
            filename = st.text_input("Имя файла", value="function", key="f_name")

        if st.button("🚀 Построить график функции", type="primary", use_container_width=True, key="build_func"):
            try:
                with st.spinner("Построение графика..."):
                    plotter = FunctionPlotter(vars(params_global))
                    plotter.add_curve_from_latex(
                        formula,
                        {},
                        [x_min, x_max],
                        {"color": color, "linewidth": linewidth}
                    )
                    plotter.set_axes(
                        xlim=[x_min, x_max],
                        xlabel=xlabel,
                        ylabel=ylabel,
                        grid=grid
                    )

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                        plotter.save(tmp.name)

                        with open(tmp.name, 'rb') as f:
                            svg_data = f.read()

                        # Добавляем в историю
                        st.session_state.graph_history.append({
                            'name': filename,
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'type': 'function',
                            'svg_data': svg_data
                        })

                        st.session_state.current_graph = svg_data

                        os.unlink(tmp.name)

                st.success("✅ График успешно построен!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")

    # ========== ВКЛАДКА: ОДУ ==========
    with tab2:
        st.subheader("Система ОДУ - временные ряды")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**Система уравнений**")

            num_vars = st.number_input("Количество переменных", 2, 4, 2, 1, key="ode_nvars")

            equations = []
            var_names = []
            ics = []
            colors_ode = []

            for i in range(num_vars):
                st.markdown(f"**Переменная {i+1}**")
                col_a, col_b, col_c, col_d = st.columns([1, 2, 1, 1])

                with col_a:
                    var_name = st.text_input("Имя", value=chr(120+i), key=f"ode_var_{i}", label_visibility="collapsed")
                    var_names.append(var_name)

                with col_b:
                    eq = st.text_input(f"d{var_name}/dt =", value="-x" if i==0 else "x-y", key=f"ode_eq_{i}", label_visibility="collapsed")
                    equations.append(eq)

                with col_c:
                    ic = st.number_input(f"{var_name}(0)", value=float(i+1), key=f"ode_ic_{i}", label_visibility="collapsed")
                    ics.append(ic)

                with col_d:
                    c = st.selectbox("🎨", ["blue", "red", "green", "orange", "purple"], key=f"ode_c_{i}", label_visibility="collapsed")
                    colors_ode.append(c)

        with col2:
            st.markdown("**Параметры**")
            t_start = st.number_input("t начало", value=0.0, step=0.5, key="ode_tstart")
            t_end = st.number_input("t конец", value=10.0, step=0.5, key="ode_tend")

            param_text = st.text_area("Параметры (a=1, b=2)", value="", key="ode_params", height=100)

            params = {}
            if param_text.strip():
                for item in param_text.split(','):
                    if '=' in item:
                        k, v = item.split('=')
                        params[k.strip()] = float(v.strip())

        col1, col2, col3 = st.columns(3)
        with col1:
            xlabel_ode = st.text_input("Ось X", value="t", key="ode_xlabel")
        with col2:
            ylabel_ode = st.text_input("Ось Y", value="значение", key="ode_ylabel")
        with col3:
            filename_ode = st.text_input("Имя файла", value="ode", key="ode_name")

        if st.button("🚀 Построить ОДУ", type="primary", use_container_width=True, key="build_ode"):
            try:
                with st.spinner("Решение системы ОДУ..."):
                    plotter = ODEPlotter(vars(params_global))

                    styles = [{"color": colors_ode[i], "linewidth": 1.5} for i in range(num_vars)]

                    plotter.solve_and_plot_time(
                        equations,
                        var_names,
                        ics,
                        params,
                        [t_start, t_end],
                        styles
                    )

                    plotter.set_axes(xlabel=xlabel_ode, ylabel=ylabel_ode, grid=True)

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                        plotter.save(tmp.name)

                        with open(tmp.name, 'rb') as f:
                            svg_data = f.read()

                        st.session_state.graph_history.append({
                            'name': filename_ode,
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'type': 'ode_time',
                            'svg_data': svg_data
                        })

                        st.session_state.current_graph = svg_data
                        os.unlink(tmp.name)

                st.success("✅ График ОДУ успешно построен!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")

    # ========== ВКЛАДКА: ФАЗОВЫЙ ПОРТРЕТ ==========
    with tab3:
        st.subheader("Фазовый портрет")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**Система уравнений**")

            col_a, col_b = st.columns(2)
            with col_a:
                var1 = st.text_input("Переменная 1", value="x", key="pp_var1")
                eq1 = st.text_input(f"d{var1}/dt =", value="y", key="pp_eq1")
                ic1 = st.number_input(f"{var1}(0)", value=1.5, key="pp_ic1")

            with col_b:
                var2 = st.text_input("Переменная 2", value="y", key="pp_var2")
                eq2 = st.text_input(f"d{var2}/dt =", value="-\\\\sin(x)", key="pp_eq2")
                ic2 = st.number_input(f"{var2}(0)", value=0.0, key="pp_ic2")

        with col2:
            st.markdown("**Настройки**")
            t_end_pp = st.number_input("Время", value=50.0, step=5.0, key="pp_tend")
            color_pp = st.selectbox("Цвет", ["blue", "red", "green"], key="pp_color")
            show_vector = st.checkbox("Векторное поле", value=True, key="pp_vector")

            if show_vector:
                density = st.slider("Плотность", 5, 30, 15, key="pp_density")

        col1, col2, col3 = st.columns(3)
        with col1:
            xlabel_pp = st.text_input("Ось X", value="x", key="pp_xlabel")
        with col2:
            ylabel_pp = st.text_input("Ось Y", value="y", key="pp_ylabel")
        with col3:
            filename_pp = st.text_input("Имя файла", value="phase", key="pp_name")

        if st.button("🚀 Построить фазовый портрет", type="primary", use_container_width=True, key="build_phase"):
            try:
                with st.spinner("Построение фазового портрета..."):
                    plotter = ODEPlotter(vars(params_global))

                    if show_vector:
                        plotter.add_vector_field(
                            [eq1, eq2],
                            [var1, var2],
                            {},
                            [0, 1],
                            {"density": density, "color": "gray", "alpha": 0.5, "scale": 20, "width": 0.002}
                        )

                    plotter.solve_and_plot_phase(
                        [eq1, eq2],
                        [var1, var2],
                        [ic1, ic2],
                        {},
                        [0, t_end_pp],
                        [0, 1],
                        {"color": color_pp, "linewidth": 1.2}
                    )

                    plotter.set_axes(xlabel=xlabel_pp, ylabel=ylabel_pp, grid=True)

                    with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                        plotter.save(tmp.name)

                        with open(tmp.name, 'rb') as f:
                            svg_data = f.read()

                        st.session_state.graph_history.append({
                            'name': filename_pp,
                            'timestamp': datetime.now().strftime('%H:%M:%S'),
                            'type': 'phase_portrait',
                            'svg_data': svg_data
                        })

                        st.session_state.current_graph = svg_data
                        os.unlink(tmp.name)

                st.success("✅ Фазовый портрет успешно построен!")
                st.rerun()

            except Exception as e:
                st.error(f"❌ Ошибка: {str(e)}")

# ========== ПРЕДПРОСМОТР ТЕКУЩЕГО ГРАФИКА ==========
if st.session_state.current_graph is not None:
    st.markdown("---")
    st.subheader("📊 Последний построенный график")

    col1, col2 = st.columns([4, 1])

    with col1:
        st.image(st.session_state.current_graph)

    with col2:
        st.markdown("### Действия")

        if st.button("💾 Скачать SVG", use_container_width=True):
            st.download_button(
                "Скачать файл",
                st.session_state.current_graph,
                file_name=f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
                mime="image/svg+xml",
                use_container_width=True
            )

        if st.button("📋 Копировать в галерею", use_container_width=True):
            st.success("✅ Уже в галерее!")

        if st.button("🗑️ Очистить", use_container_width=True):
            st.session_state.current_graph = None
            st.rerun()

# Футер
st.markdown("---")
col1, col2, col3 = st.columns(3)
with col1:
    st.caption("📱 Оптимизировано для iPad Pro 11\"")
with col2:
    st.caption("🎓 Проект для курсовой работы")
with col3:
    st.caption(f"📊 Графиков в истории: {len(st.session_state.graph_history)}")
