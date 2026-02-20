import streamlit as st
import sys
import os
import tempfile
import pandas as pd
from datetime import datetime

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
        "",
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
                            st.image(graph['svg_data'], width="stretch")

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
                progress = st.progress(0)
                for idx in range(len(df)):
                    progress.progress((idx + 1) / len(df))
                    st.session_state.graph_history.append({
                        'name': f"graph_{idx}",
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'type': 'excel'
                    })
                progress.empty()
                st.success(f"Построено графиков: {len(df)}")

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
            color = st.selectbox("Цвет", ["blue", "red", "green", "purple", "orange"])
            linewidth = st.slider("Толщина", 0.5, 4.0, 2.0)

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
                    plotter = FunctionPlotter(vars(params_global))
                    plotter.add_curve_from_latex(
                        formula, {}, [x_min, x_max],
                        {"color": color, "linewidth": linewidth}
                    )
                    plotter.set_axes(xlim=[x_min, x_max], xlabel=xlabel, ylabel=ylabel, grid=True)

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
                    c = st.selectbox("Цвет", ["blue", "red", "green", "orange", "purple"], key=f"c_{i}", label_visibility="collapsed")
                    colors_list.append(c)

        with col2:
            st.markdown("**Время**")
            t_start = st.number_input("Начало", value=0.0)
            t_end = st.number_input("Конец", value=10.0)

            st.markdown("**Оси**")
            xlabel_ode = st.text_input("X", value="t", key="xlabel_ode")
            ylabel_ode = st.text_input("Y", value="значение", key="ylabel_ode")
            filename_ode = st.text_input("Файл", value="ode", key="file_ode")

        if st.button("Построить", type="primary", width="stretch", key="build_ode"):
            try:
                with st.spinner("Решение системы ОДУ..."):
                    plotter = ODEPlotter(vars(params_global))
                    styles = [{"color": colors_list[i], "linewidth": 2.0} for i in range(num_vars)]

                    plotter.solve_and_plot_time(
                        equations, var_names, ics, {},
                        [t_start, t_end], styles
                    )
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
                eq1 = st.text_input(f"d{var1}/dt", value="y")
                ic1 = st.number_input(f"{var1}(0)", value=1.5)

            with col_b:
                var2 = st.text_input("Переменная 2", value="y")
                eq2 = st.text_input(f"d{var2}/dt", value="-\\\\sin(x)")
                ic2 = st.number_input(f"{var2}(0)", value=0.0)

        with col2:
            st.markdown("**Настройки**")
            t_end_pp = st.number_input("Время", value=50.0, step=5.0)
            color_pp = st.selectbox("Цвет", ["blue", "red", "green", "purple"])
            show_vector = st.checkbox("Векторное поле", value=True)

            if show_vector:
                density = st.slider("Плотность", 5, 30, 15)

            xlabel_pp = st.text_input("Ось X", value="x", key="xlabel_pp")
            ylabel_pp = st.text_input("Ось Y", value="y", key="ylabel_pp")
            filename_pp = st.text_input("Файл", value="phase", key="file_pp")

        if st.button("Построить", type="primary", width="stretch", key="build_phase"):
            try:
                with st.spinner("Построение фазового портрета..."):
                    plotter = ODEPlotter(vars(params_global))

                    if show_vector:
                        plotter.add_vector_field(
                            [eq1, eq2], [var1, var2], {}, [0, 1],
                            {"density": density, "color": "gray", "alpha": 0.4}
                        )

                    plotter.solve_and_plot_phase(
                        [eq1, eq2], [var1, var2], [ic1, ic2], {},
                        [0, t_end_pp], [0, 1],
                        {"color": color_pp, "linewidth": 2.0}
                    )
                    plotter.set_axes(xlabel=xlabel_pp, ylabel=ylabel_pp, grid=True)

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
        st.image(st.session_state.current_graph, width="stretch")

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
st.caption(f"Graph Builder | Графиков построено: {len(st.session_state.graph_history)}")
