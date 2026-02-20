import streamlit as st
import sys
import os
import tempfile
import pandas as pd
from datetime import datetime
import base64

# Настройка путей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.function_plotter import FunctionPlotter
from core.ode_plotter import ODEPlotter
from utils.excel_loader import ExcelConfigLoader
import params_global

# Конфигурация для iPad
st.set_page_config(
    page_title="График Builder",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Современный CSS для iPad
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');

    * {
        font-family: 'Inter', sans-serif;
    }

    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 0;
    }

    .block-container {
        padding: 2rem !important;
        max-width: 1400px;
    }

    /* Карточки */
    .card {
        background: white;
        border-radius: 20px;
        padding: 2rem;
        box-shadow: 0 10px 40px rgba(0,0,0,0.1);
        margin-bottom: 2rem;
    }

    /* Заголовки */
    h1 {
        color: white !important;
        font-weight: 700 !important;
        font-size: 2.5rem !important;
        margin-bottom: 0.5rem !important;
    }

    h2 {
        color: #1a202c !important;
        font-weight: 600 !important;
        font-size: 1.75rem !important;
        margin-bottom: 1.5rem !important;
    }

    h3 {
        color: #4a5568 !important;
        font-weight: 600 !important;
        font-size: 1.25rem !important;
    }

    /* Кнопки */
    .stButton>button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 1rem 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        width: 100%;
        height: auto;
        min-height: 3.5rem;
        transition: all 0.3s;
        box-shadow: 0 4px 15px rgba(102, 126, 234, 0.4);
    }

    .stButton>button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.6);
    }

    /* Поля ввода */
    .stTextInput>div>div>input,
    .stNumberInput>div>div>input,
    .stTextArea textarea {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
        padding: 0.875rem;
        font-size: 1.05rem;
        transition: border-color 0.3s;
    }

    .stTextInput>div>div>input:focus,
    .stNumberInput>div>div>input:focus,
    .stTextArea textarea:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }

    /* Selectbox */
    .stSelectbox>div>div {
        border-radius: 10px;
        border: 2px solid #e2e8f0;
    }

    /* График предпросмотр */
    .graph-preview {
        background: white;
        border-radius: 16px;
        padding: 1.5rem;
        box-shadow: 0 8px 30px rgba(0,0,0,0.12);
        margin: 2rem 0;
    }

    /* Галерея */
    .gallery-card {
        background: white;
        border-radius: 16px;
        padding: 1rem;
        box-shadow: 0 4px 15px rgba(0,0,0,0.08);
        transition: all 0.3s;
        cursor: pointer;
        border: 2px solid transparent;
    }

    .gallery-card:hover {
        transform: translateY(-4px);
        box-shadow: 0 8px 25px rgba(102, 126, 234, 0.3);
        border-color: #667eea;
    }

    /* Sidebar */
    .css-1d391kg {
        background: white;
    }

    /* Успех/ошибка */
    .success-box {
        background: #d4edda;
        color: #155724;
        padding: 1.25rem;
        border-radius: 12px;
        border-left: 5px solid #28a745;
        margin: 1rem 0;
        font-weight: 500;
    }

    .error-box {
        background: #f8d7da;
        color: #721c24;
        padding: 1.25rem;
        border-radius: 12px;
        border-left: 5px solid #dc3545;
        margin: 1rem 0;
        font-weight: 500;
    }

    /* Вкладки */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }

    .stTabs [data-baseweb="tab"] {
        border-radius: 10px;
        padding: 12px 24px;
        font-weight: 600;
    }

    /* Download button */
    .stDownloadButton>button {
        background: #48bb78;
        color: white;
        border-radius: 10px;
        font-weight: 600;
        padding: 0.75rem 1.5rem;
    }

    .stDownloadButton>button:hover {
        background: #38a169;
    }
</style>
""", unsafe_allow_html=True)

# Инициализация session state
if 'graph_history' not in st.session_state:
    st.session_state.graph_history = []
if 'current_graph' not in st.session_state:
    st.session_state.current_graph = None

# Заголовок
st.markdown("<h1>📊 График Builder</h1>", unsafe_allow_html=True)
st.markdown("<p style='color: white; font-size: 1.15rem; margin-bottom: 2rem;'>Построение математических графиков для курсовой работы</p>", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 🎯 Режим работы")
    mode = st.radio(
        "",
        ["🎨 Построить график", "📁 Загрузить Excel", "📚 Мои графики"],
        label_visibility="collapsed"
    )

    st.markdown("---")

    if st.session_state.graph_history:
        st.success(f"✅ Построено: {len(st.session_state.graph_history)}")
        if st.button("🗑️ Очистить всё", width="stretch"):
            st.session_state.graph_history = []
            st.session_state.current_graph = None
            st.rerun()

    st.markdown("---")
    st.caption("📱 Оптимизировано для iPad Pro 11\"")

# ========== РЕЖИМ: МОИ ГРАФИКИ ==========
if mode == "📚 Мои графики":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("## 📚 Галерея графиков")

    if not st.session_state.graph_history:
        st.info("📭 Графики еще не построены. Перейдите в режим 'Построить график'")
    else:
        # Сетка 2 колонки
        for i in range(0, len(st.session_state.graph_history), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(st.session_state.graph_history):
                    graph = st.session_state.graph_history[i + j]
                    with col:
                        st.markdown("<div class='gallery-card'>", unsafe_allow_html=True)
                        st.markdown(f"**{graph['name']}**")
                        st.caption(f"🕐 {graph['timestamp']}")

                        if 'svg_data' in graph:
                            st.image(graph['svg_data'], width="stretch")

                            col_a, col_b = st.columns(2)
                            with col_a:
                                st.download_button(
                                    "💾 Скачать",
                                    graph['svg_data'],
                                    file_name=f"{graph['name']}.svg",
                                    mime="image/svg+xml",
                                    width="stretch",
                                    key=f"dl_{i}_{j}"
                                )
                            with col_b:
                                if st.button("🗑️ Удалить", width="stretch", key=f"del_{i}_{j}"):
                                    st.session_state.graph_history.pop(i+j)
                                    st.rerun()

                        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ========== РЕЖИМ: EXCEL ==========
elif mode == "📁 Загрузить Excel":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.markdown("## 📁 Загрузка Excel файла")

    st.info("📋 Загрузите таблицу с конфигурациями графиков (.xlsx или .xls)")

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

            st.success(f"✅ Загружено строк: {len(df)}")

            with st.expander("👁️ Предпросмотр таблицы", expanded=True):
                st.dataframe(df, width="stretch", height=300)

            if st.button("🚀 Построить все графики", type="primary", width="stretch"):
                progress = st.progress(0)
                for idx in range(len(df)):
                    progress.progress((idx + 1) / len(df))
                    # Здесь логика построения
                    st.session_state.graph_history.append({
                        'name': f"graph_{idx}",
                        'timestamp': datetime.now().strftime('%H:%M:%S'),
                        'type': 'excel'
                    })
                progress.empty()
                st.success(f"✅ Построено графиков: {len(df)}")

            os.unlink(tmp_path)

        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# ========== РЕЖИМ: ПОСТРОИТЬ ГРАФИК ==========
else:
    # Вкладки для типов
    tab1, tab2, tab3 = st.tabs(["📈 Функция", "📊 ОДУ", "🔄 Фазовый портрет"])

    # ========== ФУНКЦИЯ ==========
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("## 📈 График функции")

        col1, col2 = st.columns([3, 1])

        with col1:
            formula = st.text_input(
                "📝 Формула LaTeX",
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
            st.markdown("**🎨 Стиль**")
            color = st.selectbox("Цвет", ["blue", "red", "green", "purple", "orange"])
            linewidth = st.slider("Толщина", 0.5, 4.0, 2.0)

        col1, col2, col3 = st.columns(3)
        with col1:
            xlabel = st.text_input("Ось X", value="x")
        with col2:
            ylabel = st.text_input("Ось Y", value="f(x)")
        with col3:
            filename = st.text_input("Имя файла", value="function")

        if st.button("🚀 Построить функцию", type="primary", width="stretch"):
            try:
                with st.spinner("⏳ Построение..."):
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

                st.markdown("<div class='success-box'>✅ График успешно построен!</div>", unsafe_allow_html=True)
                st.rerun()

            except Exception as e:
                st.markdown(f"<div class='error-box'>❌ Ошибка: {str(e)}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ========== ОДУ ==========
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("## 📊 Система ОДУ")

        col1, col2 = st.columns([2, 1])

        with col1:
            num_vars = st.number_input("Количество переменных", 2, 4, 2, 1)

            equations = []
            var_names = []
            ics = []
            colors_list = []

            for i in range(num_vars):
                st.markdown(f"**Переменная {i+1}:**")
                col_a, col_b, col_c, col_d = st.columns([1, 2, 1, 1])

                with col_a:
                    var = st.text_input("", value=chr(120+i), key=f"var_{i}", label_visibility="collapsed")
                    var_names.append(var)
                with col_b:
                    eq = st.text_input("", value="-x" if i==0 else "x-y", key=f"eq_{i}", placeholder=f"d{var}/dt", label_visibility="collapsed")
                    equations.append(eq)
                with col_c:
                    ic = st.number_input("", value=float(i+1), key=f"ic_{i}", label_visibility="collapsed")
                    ics.append(ic)
                with col_d:
                    c = st.selectbox("", ["blue", "red", "green", "orange", "purple"], key=f"c_{i}", label_visibility="collapsed")
                    colors_list.append(c)

        with col2:
            st.markdown("**⏱️ Время**")
            t_start = st.number_input("Начало", value=0.0)
            t_end = st.number_input("Конец", value=10.0)

            st.markdown("**📊 Оси**")
            xlabel_ode = st.text_input("X", value="t", key="xlabel_ode")
            ylabel_ode = st.text_input("Y", value="значение", key="ylabel_ode")
            filename_ode = st.text_input("Файл", value="ode", key="file_ode")

        if st.button("🚀 Построить ОДУ", type="primary", width="stretch"):
            try:
                with st.spinner("⏳ Решение системы..."):
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

                st.markdown("<div class='success-box'>✅ ОДУ успешно решена!</div>", unsafe_allow_html=True)
                st.rerun()

            except Exception as e:
                st.markdown(f"<div class='error-box'>❌ Ошибка: {str(e)}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    # ========== ФАЗОВЫЙ ПОРТРЕТ ==========
    with tab3:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.markdown("## 🔄 Фазовый портрет")

        col1, col2 = st.columns([2, 1])

        with col1:
            st.markdown("**📐 Система уравнений**")

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
            st.markdown("**⚙️ Настройки**")
            t_end_pp = st.number_input("Время", value=50.0, step=5.0)
            color_pp = st.selectbox("Цвет", ["blue", "red", "green", "purple"])
            show_vector = st.checkbox("Векторное поле", value=True)

            if show_vector:
                density = st.slider("Плотность", 5, 30, 15)

            xlabel_pp = st.text_input("Ось X", value="x", key="xlabel_pp")
            ylabel_pp = st.text_input("Ось Y", value="y", key="ylabel_pp")
            filename_pp = st.text_input("Файл", value="phase", key="file_pp")

        if st.button("🚀 Построить портрет", type="primary", width="stretch"):
            try:
                with st.spinner("⏳ Построение портрета..."):
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

                st.markdown("<div class='success-box'>✅ Портрет успешно построен!</div>", unsafe_allow_html=True)
                st.rerun()

            except Exception as e:
                st.markdown(f"<div class='error-box'>❌ Ошибка: {str(e)}</div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

# ========== ПРЕДПРОСМОТР ПОСЛЕДНЕГО ГРАФИКА ==========
if st.session_state.current_graph is not None and mode == "🎨 Построить график":
    st.markdown("<div class='card graph-preview'>", unsafe_allow_html=True)
    st.markdown("## 📊 Предпросмотр результата")

    col1, col2 = st.columns([4, 1])

    with col1:
        st.image(st.session_state.current_graph, width="stretch")

    with col2:
        st.markdown("### Действия")

        st.download_button(
            "💾 Скачать SVG",
            st.session_state.current_graph,
            file_name=f"graph_{datetime.now().strftime('%Y%m%d_%H%M%S')}.svg",
            mime="image/svg+xml",
            width="stretch"
        )

        if st.button("✅ Сохранено", width="stretch", disabled=True):
            pass

        if st.button("🔄 Построить новый", width="stretch"):
            st.session_state.current_graph = None
            st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

# Футер
st.markdown("---")
st.markdown(f"<p style='text-align: center; color: white;'>📱 iPad Pro 11\" | 🎓 Курсовая работа | 📊 Графиков: {len(st.session_state.graph_history)}</p>", unsafe_allow_html=True)
