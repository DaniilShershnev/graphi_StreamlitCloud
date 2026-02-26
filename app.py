import streamlit as st
import sys
import os
import tempfile
import pandas as pd
from datetime import datetime
import base64
import io
import json

try:
    from st_aggrid import AgGrid, GridOptionsBuilder, GridUpdateMode, JsCode
    AGGRID_AVAILABLE = True
except ImportError:
    AGGRID_AVAILABLE = False

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

# Импорт системы постоянного хранения
from utils.storage import PersistentStorage

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

# CSS
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    * { font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }

    /* Основной фон — белый */
    .main, .stApp { background: #ffffff !important; }
    .block-container { padding: 1.25rem 2rem !important; max-width: 1600px; }

    /* ========== SIDEBAR — компактное меню ========== */
    section[data-testid="stSidebar"] {
        background: #f8fafc !important;
        border-right: 1px solid #e2e8f0 !important;
        min-width: 190px !important;
        max-width: 190px !important;
        overflow: hidden !important;
    }
    section[data-testid="stSidebar"] > div { overflow: hidden !important; }
    [data-testid="stSidebar"] .block-container {
        padding: 1.5rem 0 1rem 0 !important;
        overflow: hidden !important;
    }

    /* Убираем кружки у radio и делаем nav-стиль */
    .stRadio > label { display: none !important; }
    .stRadio > div { gap: 0 !important; flex-direction: column !important; }
    .stRadio > div > label {
        background: transparent !important;
        border: none !important;
        border-left: 3px solid transparent !important;
        border-radius: 0 !important;
        padding: 0.65rem 1.1rem !important;
        color: #64748b !important;
        font-weight: 400 !important;
        font-size: 0.9rem !important;
        cursor: pointer;
        transition: all 0.15s;
        width: 100%;
    }
    .stRadio > div > label:hover {
        background: #f1f5f9 !important;
        color: #334155 !important;
        border-left-color: #cbd5e1 !important;
    }
    .stRadio > div > label[data-checked="true"] {
        background: #eff6ff !important;
        color: #2563eb !important;
        border-left-color: #2563eb !important;
        font-weight: 600 !important;
    }
    /* Скрыть radio-кружок */
    .stRadio > div > label > div:first-child { display: none !important; }

    /* Скрыть .card артефакты (это inline-div без реального содержимого) */
    .card { display: none !important; }
    .gallery-card { display: none !important; }

    /* ========== Кнопки ========== */
    .stButton > button {
        background: #2563eb;
        color: white;
        border: none;
        border-radius: 7px;
        padding: 0.6rem 1.2rem;
        font-size: 0.9rem;
        font-weight: 500;
        width: 100%;
        min-height: 2.6rem;
        transition: background 0.2s;
    }
    .stButton > button:hover { background: #1d4ed8; }
    .stButton > button[kind="primary"] { background: #10b981; font-weight: 600; }
    .stButton > button[kind="primary"]:hover { background: #059669; }

    /* Download button */
    .stDownloadButton > button {
        background: #10b981; color: white; border-radius: 7px;
        font-weight: 500; min-height: 2.6rem;
    }
    .stDownloadButton > button:hover { background: #059669; }

    /* ========== Поля ввода ========== */
    .stTextInput > div > div > input,
    .stNumberInput > div > div > input,
    .stTextArea textarea {
        border-radius: 7px;
        border: 1px solid #d1d5db;
        padding: 0.6rem 0.75rem;
        font-size: 0.9rem;
        background: white;
    }
    .stTextInput > div > div > input:focus,
    .stNumberInput > div > div > input:focus {
        border-color: #2563eb;
        box-shadow: 0 0 0 2px rgba(37,99,235,0.12);
    }
    .stSelectbox > div > div {
        border-radius: 7px;
        border: 1px solid #d1d5db;
        background: white;
    }

    /* ========== Tabs ========== */
    .stTabs [data-baseweb="tab-list"] {
        gap: 0.25rem;
        border-bottom: 1px solid #e5e7eb;
        margin-bottom: 1rem;
    }
    .stTabs [data-baseweb="tab"] {
        padding: 0.6rem 1.25rem;
        font-weight: 500;
        font-size: 0.9rem;
        color: #6b7280;
        border-radius: 6px 6px 0 0;
        border-bottom: 2px solid transparent;
    }
    .stTabs [data-baseweb="tab"]:hover { color: #374151; background: #f9fafb; }
    .stTabs [data-baseweb="tab"][aria-selected="true"] {
        color: #2563eb;
        border-bottom-color: #2563eb;
        background: transparent;
    }

    /* Выравнивание колонок по верху */
    [data-testid="stHorizontalBlock"] { align-items: flex-start !important; }
    [data-testid="column"] { padding-top: 0 !important; }

    /* Убрать лишние вертикальные отступы */
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"] { gap: 0.4rem; }

    /* Прогресс */
    .stProgress > div > div { background: #2563eb; }

    /* Dataframe */
    .stDataFrame { border: 1px solid #e5e7eb; border-radius: 7px; }

    /* Кнопка открытия боковой панели — прижата к левому краю */
    [data-testid="collapsedControl"] {
        position: fixed !important;
        left: 0 !important;
        top: 0 !important;
        margin: 0 !important;
        z-index: 9999 !important;
    }
    /* На случай если обёртка сдвигает кнопку */
    [data-testid="collapsedControl"] > * {
        margin: 0 !important;
    }
</style>
""", unsafe_allow_html=True)

# Глобальный JS: только подавление клавиатуры в selectbox/combobox главного фрейма
# (AG Grid находится в iframe — его логика перенесена в onGridReady)
st.markdown("""
<script>
(function() {
    function noKeyboardOnSelects() {
        var attrs = ['inputmode', 'readonly', 'autocomplete', 'autocorrect', 'autocapitalize', 'spellcheck'];
        var vals  = ['none',      'true',     'off',          'off',         'none',            'false'];
        document.querySelectorAll(
            '[data-baseweb="select"] input, input[role="combobox"]'
        ).forEach(function(el) {
            attrs.forEach(function(a, i) { el.setAttribute(a, vals[i]); });
        });
    }
    var obs = new MutationObserver(noKeyboardOnSelects);
    obs.observe(document.body, {childList: true, subtree: true});
    noKeyboardOnSelects();
    // Применяем перед каждым касанием — устраняет race condition при открытии expander
    document.addEventListener('pointerdown', noKeyboardOnSelects, true);
})();
</script>
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
    "Оливковый": "olive",
    "Бирюзовый": "teal",
    "Коралловый": "coral",
    "Золотой": "gold",
    "Темно-красный": "darkred",
    "Лазурный": "deepskyblue",
    "Малиновый": "crimson",
    "Темно-зеленый": "darkgreen",
    "Индиго": "indigo",
    "Лиловый": "violet",
    "Стальной": "steelblue",
    "Томатный": "tomato",
    "Темно-оранжевый": "darkorange",
    "Светло-зеленый": "lightgreen",
    "Светло-синий": "lightskyblue",
    "Серо-синий": "slategray",
}

# Галерея готовых формул для iPad
FORMULA_TEMPLATES = {
    "Своя формула": "",
    "— Степенные —": "",
    "Квадратичная (x²)": "x^2",
    "Кубическая (x³)": "x^3",
    "Квадратный корень (√x)": "\\sqrt{x}",
    "Обратная (1/x)": "1/x",
    "— Экспоненциальные —": "",
    "Экспонента (eˣ)": "e^{x}",
    "Убывающая экспонента (e⁻ˣ)": "e^{-x}",
    "— Тригонометрические —": "",
    "Синус": "\\sin(x)",
    "Косинус": "\\cos(x)",
    "Тангенс": "\\tan(x)",
    "— Комбинированные —": "",
    "Парабола со сдвигом": "x^2 - 4*x + 3",
    "Затухающие колебания": "e^{-x} \\cdot \\cos(x)",
    "Гауссова кривая": "e^{-x^2}",
    "Синус с амплитудой": "2 \\cdot \\sin(3*x)",
}

# Шаблоны систем ОДУ
ODE_TEMPLATES = {
    "Своя система": {
        "equations": ["", ""],
        "var_names": ["x", "y"],
        "ics": [1.0, 0.0],
        "description": ""
    },
    "Гармонический осциллятор": {
        "equations": ["y", "-x"],
        "var_names": ["x", "y"],
        "ics": [1.0, 0.0],
        "description": "dx/dt = y, dy/dt = -x"
    },
    "Затухающий осциллятор": {
        "equations": ["y", "-x - 0.5*y"],
        "var_names": ["x", "y"],
        "ics": [1.0, 0.0],
        "description": "dx/dt = y, dy/dt = -x - 0.5y"
    },
    "Лотка-Вольтерра (хищник-жертва)": {
        "equations": ["x*(1 - y)", "-y*(1 - x)"],
        "var_names": ["x", "y"],
        "ics": [0.5, 0.5],
        "description": "dx/dt = x(1-y), dy/dt = -y(1-x)"
    },
    "Ван-дер-Поль": {
        "equations": ["y", "0.5*(1 - x^2)*y - x"],
        "var_names": ["x", "y"],
        "ics": [2.0, 0.0],
        "description": "Нелинейный осциллятор с самовозбуждением"
    },
    "Маятник (малые углы)": {
        "equations": ["y", "-\\sin(x)"],
        "var_names": ["x", "y"],
        "ics": [1.5, 0.0],
        "description": "dx/dt = y, dy/dt = -sin(x)"
    }
}

# Предустановленные имена переменных
VARIABLE_NAMES = ["x", "y", "s", "w", "t", "theta", "r", "alpha", "beta", "u", "v"]

# Предустановленные метки осей
AXIS_LABELS = {
    "x": ["x", "t", "s", "theta", "r"],
    "y": ["y", "f(x)", "s(t)", "w(t)", "r(t)", "value"]
}

# Инициализация системы постоянного хранения
@st.cache_resource
def get_storage():
    """Создание единственного экземпляра хранилища"""
    return PersistentStorage()

storage = get_storage()

# Session state с автозагрузкой из постоянного хранилища
if 'data_loaded' not in st.session_state:
    st.session_state.data_loaded = False

if not st.session_state.data_loaded:
    # Загружаем данные из постоянного хранилища при первом запуске
    st.session_state.saved_excel_configs = storage.load_excel_configs()
    st.session_state.graph_history = storage.load_graphs()
    st.session_state.data_loaded = True

if 'current_graph' not in st.session_state:
    st.session_state.current_graph = None
if 'saved_manual_configs' not in st.session_state:
    st.session_state.saved_manual_configs = {}  # {name: config_dict}

# Sidebar
with st.sidebar:
    st.markdown("<div style='padding:0.75rem 1.1rem 0.5rem;font-size:0.7rem;font-weight:600;color:#94a3b8;letter-spacing:0.08em;text-transform:uppercase;'>Навигация</div>", unsafe_allow_html=True)
    mode = st.radio(
        "Навигация",
        ["Построить график", "Загрузить Excel", "Мои графики", "Библиотека"],
        label_visibility="collapsed"
    )

    if st.session_state.graph_history:
        st.markdown("<div style='height:1px;background:#e2e8f0;margin:0.75rem 0;'></div>", unsafe_allow_html=True)
        if st.button("Очистить графики", use_container_width=True):
            storage.clear_all_graphs()
            st.session_state.graph_history = []
            st.session_state.current_graph = None
            st.rerun()

# ========== МОИ ГРАФИКИ ==========
if mode == "Мои графики":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("Галерея графиков")

    if not st.session_state.graph_history:
        st.info("Графики еще не построены. Перейдите в режим 'Построить график'")
    else:
        # Фильтры и поиск
        col1, col2, col3 = st.columns([2, 1, 1])
        with col1:
            search_query = st.text_input("🔍 Поиск по имени", placeholder="Введите название графика", label_visibility="collapsed")
        with col2:
            filter_type = st.selectbox("Тип", ["Все"] + list(set([g.get('type', 'unknown') for g in st.session_state.graph_history])), label_visibility="collapsed")
        with col3:
            sort_by = st.selectbox("Сортировка", ["Новые первые", "Старые первые", "По имени"], label_visibility="collapsed")

        # Фильтрация
        filtered_graphs = st.session_state.graph_history.copy()

        if search_query:
            filtered_graphs = [g for g in filtered_graphs if search_query.lower() in g['name'].lower()]

        if filter_type != "Все":
            filtered_graphs = [g for g in filtered_graphs if g.get('type', 'unknown') == filter_type]

        # Сортировка
        if sort_by == "Старые первые":
            filtered_graphs = list(reversed(filtered_graphs))
        elif sort_by == "По имени":
            filtered_graphs = sorted(filtered_graphs, key=lambda g: g['name'])

        st.caption(f"Найдено: {len(filtered_graphs)}")

        for i in range(0, len(filtered_graphs), 2):
            cols = st.columns(2)
            for j, col in enumerate(cols):
                if i + j < len(filtered_graphs):
                    graph = filtered_graphs[i + j]
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
                                    # Удаляем из постоянного хранилища
                                    storage.delete_graph(graph['name'], graph['timestamp'])
                                    # Находим и удаляем график из оригинального списка
                                    st.session_state.graph_history = [g for g in st.session_state.graph_history if not (g['name'] == graph['name'] and g['timestamp'] == graph['timestamp'])]
                                    st.rerun()

                        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("</div>", unsafe_allow_html=True)

# ========== БИБЛИОТЕКА ==========
elif mode == "Библиотека":
    st.markdown("<div class='card'>", unsafe_allow_html=True)
    st.subheader("📚 Библиотека сохраненных данных")

    tab1, tab2, tab3 = st.tabs(["Excel конфигурации", "Ручные настройки", "Экспорт/Импорт"])

    # TAB 1: Excel конфигурации
    with tab1:
        st.markdown("### Сохраненные Excel конфигурации")

        if not st.session_state.saved_excel_configs:
            st.info("Библиотека пуста")
        else:

            for config_name in list(st.session_state.saved_excel_configs.keys()):
                with st.expander(f"📊 {config_name}", expanded=False):
                    config_df = st.session_state.saved_excel_configs[config_name]
                    st.dataframe(config_df, use_container_width=True, height=200)

                    col1, col2, col3 = st.columns(3)
                    with col1:
                        # Скачать Excel
                        output = io.BytesIO()
                        with pd.ExcelWriter(output, engine='openpyxl') as writer:
                            config_df.to_excel(writer, index=False, sheet_name='Sheet1')
                        excel_data = output.getvalue()

                        st.download_button(
                            "⬇️ Скачать",
                            data=excel_data,
                            file_name=f"{config_name}.xlsx",
                            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                            use_container_width=True,
                            key=f"dl_excel_{config_name}"
                        )
                    with col2:
                        # Загрузить в редактор
                        if st.button("📂 Загрузить", use_container_width=True, key=f"load_excel_{config_name}"):
                            st.session_state.edited_df = config_df.copy()
                            st.success(f"✅ Загружено в редактор")
                            st.info("Перейдите в 'Загрузить Excel' для построения графиков")
                    with col3:
                        # Удалить
                        if st.button("🗑️ Удалить", use_container_width=True, key=f"del_excel_{config_name}"):
                            del st.session_state.saved_excel_configs[config_name]
                            storage.delete_excel_config(config_name)  # Удаляем с диска
                            st.rerun()

    # TAB 2: Ручные настройки (для будущего)
    with tab2:
        st.markdown("### Сохраненные ручные настройки")
        if not st.session_state.saved_manual_configs:
            st.info("📝 Здесь будут сохраняться настройки из режима 'Построить график'")
            st.caption("Функция в разработке...")
        else:
            for config_name, config_dict in st.session_state.saved_manual_configs.items():
                with st.expander(f"⚙️ {config_name}"):
                    st.json(config_dict)

    # TAB 3: Экспорт/Импорт
    with tab3:
        st.markdown("### Экспорт/Импорт библиотеки")

        st.markdown("#### 📤 Экспорт")
        st.caption("Сохраните всю библиотеку в один файл для переноса на другое устройство")

        if st.button("📦 Экспортировать библиотеку", use_container_width=True):
            # Используем встроенную функцию экспорта
            library_data = storage.export_library()

            # Добавляем ручные настройки из session_state
            library_data['manual_configs'] = st.session_state.saved_manual_configs

            library_json = json.dumps(library_data, ensure_ascii=False, indent=2)

            st.download_button(
                "⬇️ Скачать библиотеку (JSON)",
                data=library_json,
                file_name=f"graph_library_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                mime="application/json",
                use_container_width=True
            )

        st.markdown("#### 📥 Импорт")
        st.caption("Загрузите ранее сохраненную библиотеку")

        uploaded_library = st.file_uploader("Выберите JSON файл библиотеки", type=['json'])
        if uploaded_library:
            try:
                library_data = json.loads(uploaded_library.getvalue().decode('utf-8'))

                # Импортируем в постоянное хранилище
                storage.import_library(library_data, merge=False)

                # Перезагружаем данные из постоянного хранилища в session_state
                st.session_state.saved_excel_configs = storage.load_excel_configs()
                st.session_state.graph_history = storage.load_graphs()

                # Восстанавливаем ручные настройки
                st.session_state.saved_manual_configs.update(library_data.get('manual_configs', {}))

                st.success(f"✅ Библиотека загружена! Дата экспорта: {library_data.get('timestamp', 'неизвестна')}")
                st.rerun()
            except Exception as e:
                st.error(f"Ошибка при импорте: {str(e)}")

    st.markdown("</div>", unsafe_allow_html=True)

# ========== EXCEL ==========
elif mode == "Загрузить Excel":
    _modal_active = st.session_state.get('table_modal', False)

    if _modal_active:
        # В модальном режиме — сразу CSS, остальное не рендерим
        st.markdown("""<style>
            section[data-testid="stSidebar"] { display: none !important; }
            header[data-testid="stHeader"]   { display: none !important; }
            footer                           { display: none !important; }
            body, .stApp, .main             { background: white !important; }
            .main {
                padding: 0 !important;
                margin:  0 !important;
            }
            .main .block-container {
                background:    white !important;
                border-radius: 0 !important;
                padding:       4px 6px 0 6px !important;
                max-width:     100% !important;
                min-height:    100vh !important;
                box-shadow:    none !important;
            }
            /* Растягиваем iframe таблицы на весь оставшийся экран */
            iframe[title="st_aggrid.agGrid"] {
                height: calc(100vh - 56px) !important;
                min-height: calc(100vh - 56px) !important;
            }
        </style>""", unsafe_allow_html=True)
        uploaded_file = None
    else:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Загрузка Excel файла")

        # Быстрая загрузка из библиотеки (перемещаем наверх)
        if st.session_state.saved_excel_configs:
            with st.expander("📚 Быстрая загрузка из библиотеки", expanded=False):
                saved_config_name = st.selectbox(
                    "Выберите сохраненную конфигурацию",
                    ["Не выбрано"] + list(st.session_state.saved_excel_configs.keys()),
                    key="load_saved_config_top"
                )
                if saved_config_name != "Не выбрано":
                    if st.button(f"📂 Загрузить '{saved_config_name}'", use_container_width=True):
                        st.session_state.edited_df = st.session_state.saved_excel_configs[saved_config_name].copy()
                        st.session_state.current_config_name = saved_config_name
                        st.success(f"✅ Загружена конфигурация '{saved_config_name}'")
                        st.rerun()

        st.info("Загрузите таблицу с конфигурациями графиков (.xlsx или .xls)")

        uploaded_file = st.file_uploader(
            "Выберите файл",
            type=['xlsx', 'xls'],
            label_visibility="collapsed"
        )

    # Проверяем есть ли данные для редактирования (из файла или из библиотеки)
    has_data = uploaded_file is not None or 'edited_df' in st.session_state

    if uploaded_file:
        try:
            with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx') as tmp:
                tmp.write(uploaded_file.getvalue())
                tmp_path = tmp.name

            loader = ExcelConfigLoader(tmp_path)
            df = loader.load_table()
            loader.validate_table()

            # Сохраняем загруженные данные в session_state
            st.session_state.edited_df = df.copy()
            st.session_state.current_config_name = uploaded_file.name
            os.unlink(tmp_path)

            st.success(f"Загружено строк: {len(df)}")

        except Exception as e:
            st.error(f"Ошибка при загрузке файла: {str(e)}")

    # Редактор и построение графиков (работает для файла И для данных из библиотеки)
    if has_data:
        # Получаем DataFrame для редактирования
        if 'edited_df' in st.session_state:
            df = st.session_state.edited_df

            # Редактор таблицы — кнопка "Открыть редактор" открывает модальное окно-накладку
            if 'table_modal' not in st.session_state:
                st.session_state.table_modal = False

            if st.session_state.table_modal:
                # CSS уже вставлен выше; показываем только кнопку ✕
                _, _close_col = st.columns([20, 1])
                with _close_col:
                    if st.button("✕", use_container_width=True, key="btn_close_modal"):
                        st.session_state.table_modal = False
                        st.rerun()
            else:
                # Обычный режим: заголовок + кнопка открытия редактора
                _nc1, _nc2 = st.columns([8, 2])
                with _nc1:
                    st.markdown("### 📝 Редактор таблицы")
                with _nc2:
                    if st.button("⛶ Открыть редактор", use_container_width=True, key="btn_open_modal"):
                        st.session_state.table_modal = True
                        st.rerun()
                st.caption("Стилус: выделить диапазон → тап на последнюю ячейку | Палец: редактирование текста")

            color_options_excel = ["red", "blue", "green", "orange", "purple", "cyan", "magenta", "yellow", "black", "gray", "brown", "lime", "navy", "maroon", "olive", "teal", "coral", "gold", "darkred", "deepskyblue", "crimson", "darkgreen", "indigo", "violet", "steelblue", "tomato", "darkorange", "lightgreen", "lightskyblue", "slategray"]
            linestyle_options = ["-", "--", ":", "-."]
            numeric_cols = ['linewidth', 'linewidth_s', 'linewidth_w', 'x_min', 'x_max', 'xlim_min', 'xlim_max',
                           'ylim_min', 'ylim_max', 't_start', 't_end', 's0', 'w0', 'ic_1', 'ic_2',
                           'a', 'b', 'h', 'alpha', 'betta', 'beta', 'c', 'dpi']
            bool_cols = ['dual_y_axis', 'dual_y', 'two_axes', 'vector_field_enabled', 'isoclines_enabled']
            select_cols_color = ['color', 'Color', 'col', 'color_s', 'color_w']
            select_cols_ls    = ['linestyle', 'line_style', 'ls', 'linestyle_s', 'linestyle_w',
                                 'isoclines_linestyle_ds', 'isoclines_linestyle_dw']
            select_cols_type  = ['graph_type', 'type']

            _tbl_height = 1200 if st.session_state.get('table_modal', False) else 420

            if AGGRID_AVAILABLE:
                # --- AgGrid с fill handle (pen-only) и номерами строк ---
                df_display = df.copy().reset_index(drop=True)
                df_display.insert(0, '#', range(1, len(df_display) + 1))

                gb = GridOptionsBuilder.from_dataframe(df_display)
                gb.configure_column('#', headerName='#', editable=False, sortable=False,
                                    resizable=False, pinned='left', width=52,
                                    suppressFillHandle=True, cellStyle={'color': '#9ca3af', 'fontWeight': '600'})
                gb.configure_default_column(editable=True, resizable=True, sortable=False,
                                            minWidth=80, suppressFillHandle=False)

                for col in df.columns:
                    if col in select_cols_type:
                        gb.configure_column(col, cellEditor='agSelectCellEditor',
                                            cellEditorParams={'values': ["function", "ode_time", "phase_portrait"]},
                                            minWidth=100)
                    elif col in select_cols_color:
                        gb.configure_column(col, cellEditor='agSelectCellEditor',
                                            cellEditorParams={'values': color_options_excel}, minWidth=80)
                    elif col in select_cols_ls:
                        gb.configure_column(col, cellEditor='agSelectCellEditor',
                                            cellEditorParams={'values': linestyle_options}, minWidth=60)
                    elif col in numeric_cols:
                        gb.configure_column(col, type=['numericColumn'], minWidth=60)
                    elif col in bool_cols:
                        gb.configure_column(col, cellEditor='agCheckboxCellEditor',
                                            cellRenderer='agCheckboxCellRenderer', minWidth=60)

                gb.configure_grid_options(
                    enableRangeSelection=True,
                    enableFillHandle=True,
                    fillHandleDirection='xy',
                    animateRows=False,
                    # rowSelection намеренно убран — конфликтует с range selection (fill handle)
                )
                gridOptions = gb.build()

                # Вся логика стилуса — внутри onGridReady, который исполняется в iframe
                gridOptions['onGridReady'] = JsCode("""
function(params) {
    var api = params.api;
    var lastPointerType = 'touch';
    var penMoveCount = 0;  // счётчик движений стилуса — отличает tap от drag

    // === Авто-ширина столбцов по содержимому ===
    setTimeout(function() {
        try {
            var colApi = params.columnApi || params.api;
            colApi.autoSizeAllColumns(false);
        } catch(ex) {
            try { params.api.autoSizeAllColumns(false); } catch(e2) {}
        }
    }, 250);

    // === Тип указателя + сброс счётчика движений ===
    document.addEventListener('pointerdown', function(e) {
        lastPointerType = e.pointerType || 'touch';
        if (e.pointerType === 'pen') penMoveCount = 0;
    }, true);
    document.addEventListener('pointermove', function(e) {
        if (e.pointerType === 'pen') penMoveCount++;
    }, true);

    // === Клавиатура: стилус → без, палец → с ===
    document.addEventListener('focusin', function(e) {
        var el = e.target;
        if (el.tagName !== 'INPUT' && el.tagName !== 'TEXTAREA') return;
        if (lastPointerType === 'pen') {
            el.setAttribute('inputmode', 'none');
        } else {
            el.removeAttribute('inputmode');
            el.removeAttribute('readonly');
        }
    }, true);

    // =========================================================
    // === ЗАПОЛНЕНИЕ ЯЧЕЕК — три способа взаимодействия     ===
    // =========================================================

    // Общая функция заполнения диапазона значением первой строки
    function execFill(r1, r2, cols) {
        var srcNode = api.getDisplayedRowAtIndex(r1);
        if (!srcNode) return;
        api.stopEditing();
        for (var r = r1 + 1; r <= r2; r++) {
            var nd = api.getDisplayedRowAtIndex(r);
            if (!nd) continue;
            cols.forEach(function(col) {
                if (col !== '#') nd.setDataValue(col, srcNode.data[col]);
            });
        }
        api.refreshCells({ force: true });
        savedRange = null;
        fillBtn.style.display = 'none';
    }

    // --- Плавающая кнопка "↓ Заполнить" (появляется при выделении диапазона) ---
    var fillBtn = document.createElement('button');
    fillBtn.textContent = '↓ Заполнить';
    fillBtn.style.cssText = [
        'position:fixed', 'top:54px', 'right:10px', 'z-index:9999',
        'background:#1976d2', 'color:white', 'border:none', 'border-radius:10px',
        'padding:10px 18px', 'font-size:15px', 'font-weight:700',
        'cursor:pointer', 'display:none',
        'box-shadow:0 4px 18px rgba(0,0,0,0.45)',
        '-webkit-tap-highlight-color:transparent',
        'touch-action:manipulation'
    ].join(';');
    document.body.appendChild(fillBtn);

    // Сохранённый диапазон (для кнопки и "тап на последнюю ячейку")
    var savedRange = null;

    fillBtn.addEventListener('pointerup', function(e) {
        e.stopPropagation();
        if (savedRange) execFill(savedRange.r1, savedRange.r2, savedRange.cols);
    });
    fillBtn.addEventListener('click', function() {
        if (savedRange) execFill(savedRange.r1, savedRange.r2, savedRange.cols);
    });

    // Слушаем изменение диапазона → показываем/скрываем кнопку
    try {
        api.addEventListener('rangeSelectionChanged', function() {
            var ranges = api.getCellRanges();
            if (ranges && ranges.length) {
                var rng = ranges[0];
                var r1 = Math.min(rng.startRow.rowIndex, rng.endRow.rowIndex);
                var r2 = Math.max(rng.startRow.rowIndex, rng.endRow.rowIndex);
                if (r2 > r1) {
                    savedRange = { r1: r1, r2: r2, cols: rng.columns.map(function(c) { return c.getColId(); }) };
                    fillBtn.style.display = 'block';
                } else {
                    fillBtn.style.display = 'none';
                    // savedRange не очищаем — нужен для "тап на последнюю ячейку"
                }
            } else {
                fillBtn.style.display = 'none';
            }
        });
    } catch(ex) {}

    // --- Способ 2: выделить диапазон, тапнуть на последнюю ячейку → заполнить ---
    // pointerup с минимальным движением (tap) на последней строке savedRange
    document.addEventListener('pointerup', function(e) {
        if (e.pointerType !== 'pen') return;
        if (!savedRange) return;
        if (penMoveCount > 6) return; // это был drag, не tap

        var el = document.elementFromPoint(e.clientX, e.clientY);
        if (!el) return;
        var rowEl = el.closest && el.closest('.ag-row[row-index]');
        if (!rowEl) { savedRange = null; fillBtn.style.display = 'none'; return; }

        var tappedRow = parseInt(rowEl.getAttribute('row-index'), 10);
        if (isNaN(tappedRow)) return;

        if (tappedRow === savedRange.r2) {
            // Тап на последнюю строку диапазона → заполняем
            execFill(savedRange.r1, savedRange.r2, savedRange.cols);
        } else if (tappedRow < savedRange.r1 || tappedRow > savedRange.r2) {
            // Тап вне диапазона → сбрасываем
            savedRange = null;
            fillBtn.style.display = 'none';
        }
        // Тап внутри диапазона (не последняя) → ничего не делаем, savedRange остаётся
    }, true);

    // --- Способ 3: drag от fill handle уголка (для совместимости) ---
    var penFill = null;

    document.addEventListener('pointerdown', function(e) {
        var h = e.target.closest && e.target.closest('.ag-fill-handle');
        if (h && e.pointerType !== 'pen') { e.stopImmediatePropagation(); e.preventDefault(); }
    }, true);

    document.addEventListener('pointerdown', function(e) {
        if (e.pointerType !== 'pen') return;
        var h = e.target.closest && e.target.closest('.ag-fill-handle');
        if (!h) return;
        e.preventDefault(); e.stopPropagation();
        var ranges = api.getCellRanges();
        if (!ranges || !ranges.length) return;
        var rng = ranges[0];
        var r1 = rng.startRow.rowIndex, r2 = rng.endRow.rowIndex;
        if (r1 > r2) { var t = r1; r1 = r2; r2 = t; }
        penFill = { rowStart: r1, rowEnd: r2, cols: rng.columns.map(function(c) { return c.getColId(); }), targetRow: r2 };
    }, true);

    document.addEventListener('pointermove', function(e) {
        if (e.pointerType !== 'pen' || !penFill) return;
        var el = document.elementFromPoint(e.clientX, e.clientY);
        var rowEl = el && el.closest && el.closest('.ag-row[row-index]');
        if (rowEl) { penFill.targetRow = parseInt(rowEl.getAttribute('row-index'), 10); return; }
        var rows = document.querySelectorAll('.ag-row[row-index]');
        for (var i = 0; i < rows.length; i++) {
            var rect = rows[i].getBoundingClientRect();
            if (e.clientY >= rect.top && e.clientY <= rect.bottom) {
                var idx = parseInt(rows[i].getAttribute('row-index'), 10);
                if (!isNaN(idx)) { penFill.targetRow = idx; break; }
            }
        }
    }, true);

    document.addEventListener('pointerup', function(e) {
        if (e.pointerType !== 'pen' || !penFill) return;
        var state = penFill;
        penFill = null;
        setTimeout(function() {
            var curRanges = api.getCellRanges();
            var fillFrom, fillTo, srcRowIdx;
            if (curRanges && curRanges.length) {
                var cr = curRanges[0];
                var cr1 = Math.min(cr.startRow.rowIndex, cr.endRow.rowIndex);
                var cr2 = Math.max(cr.startRow.rowIndex, cr.endRow.rowIndex);
                if (cr2 > state.rowEnd) { srcRowIdx = state.rowEnd; fillFrom = state.rowEnd + 1; fillTo = cr2; }
                else if (cr1 < state.rowStart) { srcRowIdx = state.rowStart; fillFrom = cr1; fillTo = state.rowStart - 1; }
            }
            if (fillFrom === undefined) {
                if (state.targetRow > state.rowEnd) { srcRowIdx = state.rowEnd; fillFrom = state.rowEnd + 1; fillTo = state.targetRow; }
                else if (state.targetRow < state.rowStart) { srcRowIdx = state.rowStart; fillFrom = state.targetRow; fillTo = state.rowStart - 1; }
            }
            if (fillFrom !== undefined && fillTo >= fillFrom) {
                execFill(srcRowIdx, fillTo, state.cols);
            }
        }, 80);
    }, true);

    // === СЖАТИЕ APPLE PENCIL PRO → открыть редактор ячейки ===
    function openCellEditor() {
        var cell = api.getFocusedCell();
        if (!cell) return;
        api.startEditingCell({ rowIndex: cell.rowIndex, colKey: cell.column.colId });
        setTimeout(function() {
            var el = document.querySelector(
                '.ag-popup-editor select, .ag-popup-editor input, ' +
                '.ag-cell-editor select, .ag-cell-editor input'
            );
            if (el) { el.removeAttribute('inputmode'); el.focus(); el.click(); }
        }, 40);
    }

    document.addEventListener('pointerdown', function(e) {
        if (e.pointerType !== 'pen') return;
        if (e.button === 1 || e.button === 2) { e.preventDefault(); openCellEditor(); }
    }, true);

    document.addEventListener('contextmenu', function(e) {
        if (lastPointerType !== 'pen') return;
        e.preventDefault();
        openCellEditor();
    }, true);
}
""")
                # CSS применяется внутри iframe через custom_css
                ag_custom_css = {
                    # Уголок fill handle — крупный, синий, не обрезается
                    ".ag-fill-handle": {
                        "width": "20px !important",
                        "height": "20px !important",
                        "bottom": "-10px !important",
                        "right": "-10px !important",
                        "border-radius": "4px !important",
                        "background-color": "#1976d2 !important",
                        "border": "2px solid white !important",
                        "cursor": "crosshair !important",
                        "touch-action": "none !important",
                        "z-index": "9999 !important",
                        "display": "block !important",
                        "position": "absolute !important",
                    },
                    # Ячейки не должны обрезать уголок, торчащий за границу
                    ".ag-cell": {
                        "overflow": "visible !important",
                    },
                    ".ag-row": {
                        "overflow": "visible !important",
                    },
                    ".ag-center-cols-container": {
                        "overflow": "visible !important",
                    },
                }

                grid_response = AgGrid(
                    df_display,
                    gridOptions=gridOptions,
                    update_mode=GridUpdateMode.VALUE_CHANGED,
                    fit_columns_on_grid_load=False,
                    height=_tbl_height,
                    allow_unsafe_jscode=True,
                    enable_enterprise_modules=True,
                    key="excel_editor_aggrid",
                    theme='alpine',
                    custom_css=ag_custom_css,
                )

                edited_df = pd.DataFrame(grid_response['data'])
                if '#' in edited_df.columns:
                    edited_df = edited_df.drop(columns=['#'])
                # Восстанавливаем типы данных
                for col in df.columns:
                    if col in edited_df.columns:
                        try:
                            edited_df[col] = edited_df[col].astype(df[col].dtype)
                        except Exception:
                            pass
            else:
                # Fallback: стандартный st.data_editor
                column_config = {}
                for col_name in select_cols_type:
                    if col_name in df.columns:
                        column_config[col_name] = st.column_config.SelectboxColumn(
                            col_name, options=["function", "ode_time", "phase_portrait"])
                for col_name in select_cols_color:
                    if col_name in df.columns:
                        column_config[col_name] = st.column_config.SelectboxColumn(
                            col_name, options=color_options_excel)
                for col_name in select_cols_ls:
                    if col_name in df.columns:
                        column_config[col_name] = st.column_config.SelectboxColumn(
                            col_name, options=linestyle_options)
                for col_name in numeric_cols:
                    if col_name in df.columns:
                        column_config[col_name] = st.column_config.NumberColumn(col_name, format="%.4f")
                for col_name in bool_cols:
                    if col_name in df.columns:
                        column_config[col_name] = st.column_config.CheckboxColumn(col_name)
                edited_df = st.data_editor(df, column_config=column_config,
                                           num_rows="dynamic", use_container_width=True,
                                           height=400, key="excel_editor")

            # Обновляем session_state
            st.session_state.edited_df = edited_df

            # В модальном режиме — только таблица, больше ничего
            if st.session_state.get('table_modal', False):
                st.stop()

            # Кнопки управления
            col1, col2, col3 = st.columns(3)
            with col1:
                if st.button("↻ Сбросить изменения", use_container_width=True):
                    st.session_state.edited_df = df.copy()
                    st.rerun()
            with col2:
                # Экспорт в Excel
                output = io.BytesIO()
                with pd.ExcelWriter(output, engine='openpyxl') as writer:
                    edited_df.to_excel(writer, index=False, sheet_name='Sheet1')
                excel_data = output.getvalue()

                st.download_button(
                    label="⬇️ Скачать Excel",
                    data=excel_data,
                    file_name="edited_config.xlsx",
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    use_container_width=True
                )
            with col3:
                # Инициализация флага диалога сохранения
                if 'show_save_dialog' not in st.session_state:
                    st.session_state.show_save_dialog = False

                # Кнопка открытия диалога
                if st.button("💾 В библиотеку", use_container_width=True, help="Сохранить эту конфигурацию для быстрого доступа"):
                    st.session_state.show_save_dialog = not st.session_state.show_save_dialog

            # Диалог сохранения (вне колонок, чтобы занимал всю ширину)
            if st.session_state.get('show_save_dialog', False):
                with st.expander("💾 Сохранить конфигурацию в библиотеку", expanded=True):
                    col_a, col_b = st.columns([3, 1])
                    with col_a:
                        # Используем имя текущей конфигурации (из файла или библиотеки)
                        default_name = st.session_state.get('current_config_name', 'config').replace('.xlsx', '').replace('.xls', '')
                        save_name = st.text_input(
                            "Имя конфигурации",
                            value=default_name,
                            key="save_config_name"
                        )
                    with col_b:
                        st.write("")  # Отступ
                        st.write("")  # Отступ для выравнивания
                        if st.button("✅ Сохранить", key="save_confirm", type="primary"):
                            if save_name and save_name.strip():
                                # Сохраняем в session_state
                                st.session_state.saved_excel_configs[save_name.strip()] = edited_df.copy()
                                # Сохраняем на диск для постоянного хранения
                                storage.save_excel_config(save_name.strip(), edited_df.copy())
                                st.success(f"✅ Конфигурация '{save_name.strip()}' сохранена в библиотеке")
                                st.session_state.show_save_dialog = False
                                st.rerun()
                            else:
                                st.error("⚠️ Введите имя конфигурации")

            if st.button("🎨 Построить все графики", type="primary", width="stretch"):
                # Используем отредактированные данные вместо оригинальных
                # Сохраняем во временный файл и загружаем заново
                with tempfile.NamedTemporaryFile(delete=False, suffix='.xlsx', mode='wb') as tmp_edited:
                    edited_df.to_excel(tmp_edited.name, index=False)
                    tmp_edited_path = tmp_edited.name

                edited_loader = ExcelConfigLoader(tmp_edited_path)
                edited_loader.load_table()
                grouped_rows = edited_loader.get_rows_grouped_by_output()
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
                                linestyle_raw = row.get('linestyle') or row.get('line_style') or row.get('ls')

                                # Проверяем на NaN/None/пустую строку
                                if linestyle_raw is None or (isinstance(linestyle_raw, float) and pd.isna(linestyle_raw)) or str(linestyle_raw).strip() == '':
                                    actual_linestyle = '-'  # По умолчанию сплошная линия
                                else:
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

                            elif graph_type == 'phase_portrait':
                                # Фазовый портрет - обрабатывается отдельно после цикла
                                pass

                        # Обработка фазового портрета (после всех строк)
                        if graph_type == 'phase_portrait':
                            # Сначала устанавливаем пределы осей
                            xlim_min = first_row.get('xlim_min', 0)
                            xlim_max = first_row.get('xlim_max', 3)
                            ylim_min = first_row.get('ylim_min', 0)
                            ylim_max = first_row.get('ylim_max', 3)
                            plotter.ax.set_xlim([xlim_min, xlim_max])
                            plotter.ax.set_ylim([ylim_min, ylim_max])

                            # Затем векторное поле (если включено)
                            vector_field_enabled = first_row.get('vector_field_enabled')
                            if vector_field_enabled and str(vector_field_enabled).lower() in ('true', 'yes', '1'):
                                eq1 = first_row.get('equation_1', 'x')
                                eq2 = first_row.get('equation_2', 'y')
                                equations = [eq1, eq2]
                                var_names = ['s', 'w']

                                params = {}
                                param_cols = ['a', 'b', 'h', 'alpha', 'betta', 'beta', 'c']
                                for param_name in param_cols:
                                    if param_name in first_row and first_row[param_name] is not None:
                                        params[param_name] = first_row[param_name]

                                field_config = {
                                    'density': int(first_row.get('vector_field_density', 50)),
                                    'color': first_row.get('vector_field_color', 'lightgray'),
                                    'alpha': float(first_row.get('vector_field_alpha', 0.5))
                                }

                                plotter.add_vector_field(
                                    equations, var_names, params,
                                    [0, 1],  # var_indices для s и w
                                    field_config
                                )

                            # Затем изоклины (если включены)
                            isoclines_enabled = first_row.get('isoclines_enabled')
                            if isoclines_enabled and str(isoclines_enabled).lower() in ('true', 'yes', '1'):
                                eq1 = first_row.get('equation_1', 'x')
                                eq2 = first_row.get('equation_2', 'y')
                                equations = [eq1, eq2]
                                var_names = ['s', 'w']

                                params = {}
                                param_cols = ['a', 'b', 'h', 'alpha', 'betta', 'beta', 'c']
                                for param_name in param_cols:
                                    if param_name in first_row and first_row[param_name] is not None:
                                        params[param_name] = first_row[param_name]

                                isocline_config = {
                                    'linestyle_ds': first_row.get('isoclines_linestyle_ds', '--'),
                                    'linestyle_dw': first_row.get('isoclines_linestyle_dw', '--'),
                                    'color_ds': first_row.get('isoclines_color_ds', 'black'),
                                    'color_dw': first_row.get('isoclines_color_dw', 'darkred'),
                                    'linewidth_ds': float(first_row.get('isoclines_linewidth_ds', 1.5)),
                                    'linewidth_dw': float(first_row.get('isoclines_linewidth_dw', 1.5))
                                }

                                plotter.add_isoclines(
                                    equations, var_names, params,
                                    [0, 1],  # var_indices для s и w
                                    isocline_config
                                )

                            # Наконец, строим траектории для каждой строки
                            for row in rows:
                                eq1 = row.get('equation_1', 'x')
                                eq2 = row.get('equation_2', 'y')
                                equations = [eq1, eq2]
                                var_names = ['s', 'w']

                                # Начальные условия
                                ic_s = row.get('s0', 1.0)
                                ic_w = row.get('w0', 0.0)
                                ics = [ic_s, ic_w]

                                # Параметры
                                params = {}
                                param_cols = ['a', 'b', 'h', 'alpha', 'betta', 'beta', 'c']
                                for param_name in param_cols:
                                    if param_name in row and row[param_name] is not None:
                                        params[param_name] = row[param_name]

                                # Время
                                t_start = row.get('t_start', 0)
                                t_end = row.get('t_end', 100)

                                # Стиль траектории
                                color_s = row.get('color_s', 'red')
                                linewidth_s = row.get('linewidth_s', 0.6)
                                linestyle_s_raw = row.get('linestyle_s', '-')

                                # Маппинг linestyle
                                linestyle_map = {'-': '-', '--': '--', ':': ':', '-.': '-.'}
                                linestyle_s = linestyle_map.get(str(linestyle_s_raw).strip(), '-')

                                style = {
                                    "color": color_s,
                                    "linewidth": linewidth_s,
                                    "linestyle": linestyle_s
                                }

                                # Добавляем траекторию используя правильный метод
                                plotter.solve_and_plot_phase(
                                    equations_latex=equations,
                                    variable_names=var_names,
                                    initial_conditions=ics,
                                    params=params,
                                    t_span=[t_start, t_end],
                                    var_indices=[0, 1],  # s и w
                                    style=style,
                                    solver_method=row.get('solver_method', 'RK45')
                                )

                        # Настраиваем оси
                        xlabel = first_row.get('xlabel', 't' if graph_type != 'phase_portrait' else 's')
                        ylabel = first_row.get('ylabel', 'value' if graph_type != 'phase_portrait' else 'w')

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
                        elif graph_type == 'phase_portrait':
                            # Для фазового портрета xlim и ylim уже установлены выше
                            # Настраиваем только подписи и сетку
                            plotter.set_axes(
                                xlabel=xlabel,
                                ylabel=ylabel,
                                grid=True
                            )
                        else:
                            plotter.set_axes(xlabel=xlabel, ylabel=ylabel, grid=True)

                        # Сохраняем в SVG
                        with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                            plotter.save(tmp.name)
                            with open(tmp.name, 'rb') as f:
                                svg_data = f.read()

                            timestamp_str = datetime.now().strftime('%H:%M:%S')
                            st.session_state.graph_history.append({
                                'name': output_file,
                                'timestamp': timestamp_str,
                                'type': graph_type,
                                'svg_data': svg_data
                            })
                            # Сохраняем на диск для постоянного хранения
                            storage.save_graph(output_file, timestamp_str, graph_type, svg_data)
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

                # Удаляем временный файл с отредактированными данными
                os.unlink(tmp_edited_path)

    st.markdown("</div>", unsafe_allow_html=True)

# ========== ПОСТРОИТЬ ГРАФИК ==========
else:
    tab1, tab2, tab3 = st.tabs(["Функция", "ОДУ", "Фазовый портрет"])

    # ========== ФУНКЦИЯ ==========
    with tab1:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("График функции")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Галерея готовых формул
            formula_template = st.selectbox(
                "Выберите формулу",
                options=list(FORMULA_TEMPLATES.keys()),
                index=0,
                help="Выберите из галереи или укажите свою"
            )

            # Если выбран разделитель (строка начинается с —), показываем предупреждение
            if formula_template.startswith("—"):
                st.warning("Выберите формулу из списка ниже")
                formula = ""
            elif formula_template == "Своя формула":
                formula = st.text_input(
                    "Введите формулу",
                    value="x^2",
                    placeholder="x^2 + \\\\sin(x)",
                    help="Используйте двойной слеш: \\\\sin, \\\\cos, \\\\exp"
                )
            else:
                formula = FORMULA_TEMPLATES[formula_template]
                st.code(formula, language="latex")
                # Опция для редактирования
                if st.checkbox("Редактировать формулу", key="edit_formula"):
                    formula = st.text_input(
                        "Формула LaTeX",
                        value=formula,
                        help="Используйте двойной слеш: \\\\sin, \\\\cos, \\\\exp"
                    )

            col_a, col_b = st.columns(2)
            with col_a:
                x_min = st.number_input("x min", value=-10.0, step=1.0)
            with col_b:
                x_max = st.number_input("x max", value=10.0, step=1.0)

            col_x, col_y, col_f = st.columns(3)
            with col_x:
                xlabel_choice = st.selectbox("Ось X", AXIS_LABELS["x"] + ["Своя метка"], index=0)
                if xlabel_choice == "Своя метка":
                    xlabel = st.text_input("Метка X", value="x", label_visibility="collapsed")
                else:
                    xlabel = xlabel_choice
            with col_y:
                ylabel_choice = st.selectbox("Ось Y", AXIS_LABELS["y"] + ["Своя метка"], index=1)
                if ylabel_choice == "Своя метка":
                    ylabel = st.text_input("Метка Y", value="y", label_visibility="collapsed")
                else:
                    ylabel = ylabel_choice
            with col_f:
                filename = st.text_input("Имя файла", value="function")

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
            col_sp1, col_sp2 = st.columns(2)
            with col_sp1:
                show_top_spine = st.checkbox("Верхняя", value=False, key="show_top_func")
            with col_sp2:
                show_right_spine = st.checkbox("Правая", value=False, key="show_right_func")

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

                        timestamp_str = datetime.now().strftime('%H:%M:%S')
                        st.session_state.graph_history.append({
                            'name': filename,
                            'timestamp': timestamp_str,
                            'type': 'function',
                            'svg_data': svg_data
                        })
                        # Сохраняем на диск для постоянного хранения
                        storage.save_graph(filename, timestamp_str, 'function', svg_data)
                        st.session_state.current_graph = svg_data
                        os.unlink(tmp.name)

                st.session_state.last_built_tab = "function"
                st.session_state.pop('save_name_func_inline', None)

            except Exception as e:
                st.error(f"Ошибка: {str(e)}")

        # Inline preview + сохранение в библиотеку
        if st.session_state.current_graph is not None and st.session_state.get('last_built_tab') == 'function':
            svg_b64 = base64.b64encode(st.session_state.current_graph).decode()
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{svg_b64}" style="width:100%;border-radius:8px;margin-bottom:0.75rem;">',
                unsafe_allow_html=True
            )
            g_name_f = st.session_state.graph_history[-1]['name'] if st.session_state.graph_history else "graph"
            ci1, ci2, ci3 = st.columns([3, 1, 1])
            with ci1:
                new_name_f = st.text_input("Имя в библиотеке", value=g_name_f, key="save_name_func_inline")
            with ci2:
                if st.button("💾 Сохранить", key="save_lib_func_inline", use_container_width=True, type="primary"):
                    if st.session_state.graph_history and new_name_f.strip():
                        last = st.session_state.graph_history[-1]
                        storage.delete_graph(last['name'], last['timestamp'])
                        new_ts = datetime.now().strftime('%H:%M:%S')
                        storage.save_graph(new_name_f.strip(), new_ts, last['type'], last['svg_data'])
                        st.session_state.graph_history[-1]['name'] = new_name_f.strip()
                        st.session_state.graph_history[-1]['timestamp'] = new_ts
                        st.success(f"✅ Сохранено: «{new_name_f.strip()}»")
            with ci3:
                st.download_button("⬇️ SVG", st.session_state.current_graph,
                                   file_name=f"{g_name_f}.svg", mime="image/svg+xml",
                                   use_container_width=True, key="dl_func_inline")

        st.markdown("</div>", unsafe_allow_html=True)

    # ========== ОДУ ==========
    with tab2:
        st.markdown("<div class='card'>", unsafe_allow_html=True)
        st.subheader("Система ОДУ")

        # Шаблоны систем ОДУ
        template_choice = st.selectbox(
            "Выберите шаблон системы",
            options=list(ODE_TEMPLATES.keys()),
            index=0,
            help="Выберите готовую систему или создайте свою"
        )

        template = ODE_TEMPLATES[template_choice]
        if template["description"]:
            st.info(f"📖 {template['description']}")

        col1, col2 = st.columns([2, 1])

        with col1:
            # Используем num_vars из шаблона, но позволяем редактировать для "Своя система"
            if template_choice == "Своя система":
                num_vars = st.number_input("Количество переменных", 2, 4, 2, 1)
            else:
                num_vars = len(template["equations"])

            equations = []
            var_names = []
            ics = []
            colors_list = []

            for i in range(num_vars):
                st.markdown(f"**Переменная {i+1}**")
                col_a, col_b, col_c, col_d = st.columns([1, 2, 1, 1])

                with col_a:
                    # Используем предустановленные имена переменных или из шаблона
                    default_var = template["var_names"][i] if i < len(template["var_names"]) else VARIABLE_NAMES[i]
                    var_choice = st.selectbox(
                        "Имя",
                        VARIABLE_NAMES + ["Другое"],
                        index=VARIABLE_NAMES.index(default_var) if default_var in VARIABLE_NAMES else len(VARIABLE_NAMES),
                        key=f"var_select_{i}",
                        label_visibility="collapsed"
                    )
                    if var_choice == "Другое":
                        var = st.text_input("Имя", value=default_var, key=f"var_{i}", label_visibility="collapsed")
                    else:
                        var = var_choice
                    var_names.append(var)
                with col_b:
                    default_eq = template["equations"][i] if i < len(template["equations"]) else ""
                    eq = st.text_input("Уравнение", value=default_eq, key=f"eq_{i}", label_visibility="collapsed")
                    equations.append(eq)
                with col_c:
                    default_ic = template["ics"][i] if i < len(template["ics"]) else float(i+1)
                    ic = st.number_input("Нач. усл.", value=default_ic, key=f"ic_{i}", label_visibility="collapsed")
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

            xlabel_ode_choice = st.selectbox("X", AXIS_LABELS["x"] + ["Другое"], index=1, key="xlabel_ode_select")  # t по умолчанию
            if xlabel_ode_choice == "Другое":
                xlabel_ode = st.text_input("Метка X", value="t", key="xlabel_ode", label_visibility="collapsed")
            else:
                xlabel_ode = xlabel_ode_choice

            ylabel_ode_choice = st.selectbox("Y левая", AXIS_LABELS["y"] + ["Другое"], index=5, key="ylabel_ode_select")  # value по умолчанию
            if ylabel_ode_choice == "Другое":
                ylabel_ode = st.text_input("Метка Y", value="значение", key="ylabel_ode", label_visibility="collapsed")
            else:
                ylabel_ode = ylabel_ode_choice

            if use_dual_y_manual:
                ylabel_right_ode_choice = st.selectbox("Y правая", AXIS_LABELS["y"] + ["Другое"], index=5, key="ylabel_right_ode_select")
                if ylabel_right_ode_choice == "Другое":
                    ylabel_right_ode = st.text_input("Метка Y правая", value="значение 2", key="ylabel_right_ode", label_visibility="collapsed")
                else:
                    ylabel_right_ode = ylabel_right_ode_choice
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

                        timestamp_str = datetime.now().strftime('%H:%M:%S')
                        st.session_state.graph_history.append({
                            'name': filename_ode,
                            'timestamp': timestamp_str,
                            'type': 'ode',
                            'svg_data': svg_data
                        })
                        # Сохраняем на диск для постоянного хранения
                        storage.save_graph(filename_ode, timestamp_str, 'ode', svg_data)
                        st.session_state.current_graph = svg_data
                        os.unlink(tmp.name)

                st.session_state.last_built_tab = "ode"
                st.session_state.pop('save_name_ode_inline', None)

            except Exception as e:
                st.error(f"Ошибка: {str(e)}")

        # Inline preview + сохранение в библиотеку
        if st.session_state.current_graph is not None and st.session_state.get('last_built_tab') == 'ode':
            svg_b64 = base64.b64encode(st.session_state.current_graph).decode()
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{svg_b64}" style="width:100%;border-radius:8px;margin-bottom:0.75rem;">',
                unsafe_allow_html=True
            )
            g_name_ode = st.session_state.graph_history[-1]['name'] if st.session_state.graph_history else "ode"
            ci1, ci2, ci3 = st.columns([3, 1, 1])
            with ci1:
                new_name_ode = st.text_input("Имя в библиотеке", value=g_name_ode, key="save_name_ode_inline")
            with ci2:
                if st.button("💾 Сохранить", key="save_lib_ode_inline", use_container_width=True, type="primary"):
                    if st.session_state.graph_history and new_name_ode.strip():
                        last = st.session_state.graph_history[-1]
                        storage.delete_graph(last['name'], last['timestamp'])
                        new_ts = datetime.now().strftime('%H:%M:%S')
                        storage.save_graph(new_name_ode.strip(), new_ts, last['type'], last['svg_data'])
                        st.session_state.graph_history[-1]['name'] = new_name_ode.strip()
                        st.session_state.graph_history[-1]['timestamp'] = new_ts
                        st.success(f"✅ Сохранено: «{new_name_ode.strip()}»")
            with ci3:
                st.download_button("⬇️ SVG", st.session_state.current_graph,
                                   file_name=f"{g_name_ode}.svg", mime="image/svg+xml",
                                   use_container_width=True, key="dl_ode_inline")

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
                var1_choice = st.selectbox("Переменная 1", VARIABLE_NAMES + ["Другое"], index=0, key="var1_pp_select")  # x по умолчанию
                if var1_choice == "Другое":
                    var1 = st.text_input("Имя переменной 1", value="x", key="var1_pp", label_visibility="collapsed")
                else:
                    var1 = var1_choice
                eq1 = st.text_input(f"d{var1}/dt", value="y", help="Используйте двойной слеш: \\\\sin, \\\\cos, \\\\exp")
                ic1 = st.number_input(f"{var1}(0)", value=1.5)

            with col_b:
                var2_choice = st.selectbox("Переменная 2", VARIABLE_NAMES + ["Другое"], index=1, key="var2_pp_select")  # y по умолчанию
                if var2_choice == "Другое":
                    var2 = st.text_input("Имя переменной 2", value="y", key="var2_pp", label_visibility="collapsed")
                else:
                    var2 = var2_choice
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

            xlabel_pp_choice = st.selectbox("Ось X", AXIS_LABELS["x"] + ["Другое"], index=0, key="xlabel_pp_select")  # x по умолчанию
            if xlabel_pp_choice == "Другое":
                xlabel_pp = st.text_input("Метка X", value="x", key="xlabel_pp", label_visibility="collapsed")
            else:
                xlabel_pp = xlabel_pp_choice

            ylabel_pp_choice = st.selectbox("Ось Y", AXIS_LABELS["y"] + ["Другое"], index=0, key="ylabel_pp_select")  # y по умолчанию
            if ylabel_pp_choice == "Другое":
                ylabel_pp = st.text_input("Метка Y", value="y", key="ylabel_pp", label_visibility="collapsed")
            else:
                ylabel_pp = ylabel_pp_choice

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

                        timestamp_str = datetime.now().strftime('%H:%M:%S')
                        st.session_state.graph_history.append({
                            'name': filename_pp,
                            'timestamp': timestamp_str,
                            'type': 'phase',
                            'svg_data': svg_data
                        })
                        # Сохраняем на диск для постоянного хранения
                        storage.save_graph(filename_pp, timestamp_str, 'phase', svg_data)
                        st.session_state.current_graph = svg_data
                        os.unlink(tmp.name)

                st.session_state.last_built_tab = "phase"
                st.session_state.pop('save_name_pp_inline', None)

            except Exception as e:
                st.error(f"Ошибка: {str(e)}")

        # Inline preview + сохранение в библиотеку
        if st.session_state.current_graph is not None and st.session_state.get('last_built_tab') == 'phase':
            svg_b64 = base64.b64encode(st.session_state.current_graph).decode()
            st.markdown(
                f'<img src="data:image/svg+xml;base64,{svg_b64}" style="width:100%;border-radius:8px;margin-bottom:0.75rem;">',
                unsafe_allow_html=True
            )
            g_name_pp = st.session_state.graph_history[-1]['name'] if st.session_state.graph_history else "phase"
            ci1, ci2, ci3 = st.columns([3, 1, 1])
            with ci1:
                new_name_pp = st.text_input("Имя в библиотеке", value=g_name_pp, key="save_name_pp_inline")
            with ci2:
                if st.button("💾 Сохранить", key="save_lib_pp_inline", use_container_width=True, type="primary"):
                    if st.session_state.graph_history and new_name_pp.strip():
                        last = st.session_state.graph_history[-1]
                        storage.delete_graph(last['name'], last['timestamp'])
                        new_ts = datetime.now().strftime('%H:%M:%S')
                        storage.save_graph(new_name_pp.strip(), new_ts, last['type'], last['svg_data'])
                        st.session_state.graph_history[-1]['name'] = new_name_pp.strip()
                        st.session_state.graph_history[-1]['timestamp'] = new_ts
                        st.success(f"✅ Сохранено: «{new_name_pp.strip()}»")
            with ci3:
                st.download_button("⬇️ SVG", st.session_state.current_graph,
                                   file_name=f"{g_name_pp}.svg", mime="image/svg+xml",
                                   use_container_width=True, key="dl_pp_inline")

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

        # Кнопка сохранения с пользовательским именем
        if 'show_rename_dialog' not in st.session_state:
            st.session_state.show_rename_dialog = False

        if st.button("💾 Сохранить как...", width="stretch"):
            st.session_state.show_rename_dialog = not st.session_state.show_rename_dialog

        if st.button("Построить новый", width="stretch"):
            st.session_state.current_graph = None
            st.session_state.show_rename_dialog = False

    # Диалог переименования графика
    if st.session_state.get('show_rename_dialog', False) and len(st.session_state.graph_history) > 0:
        with st.expander("💾 Сохранить график под новым именем", expanded=True):
            last_graph = st.session_state.graph_history[-1]  # Последний добавленный график

            new_name = st.text_input(
                "Новое имя графика",
                value=last_graph['name'],
                key="rename_graph_input"
            )

            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("✅ Сохранить", key="rename_confirm", type="primary", use_container_width=True):
                    if new_name and new_name.strip():
                        # Обновляем имя последнего графика
                        old_name = last_graph['name']
                        old_timestamp = last_graph['timestamp']

                        # Удаляем старый
                        storage.delete_graph(old_name, old_timestamp)

                        # Сохраняем с новым именем
                        new_timestamp = datetime.now().strftime('%H:%M:%S')
                        storage.save_graph(new_name.strip(), new_timestamp, last_graph['type'], last_graph['svg_data'])

                        # Обновляем в истории
                        st.session_state.graph_history[-1]['name'] = new_name.strip()
                        st.session_state.graph_history[-1]['timestamp'] = new_timestamp

                        st.success(f"✅ График сохранен как '{new_name.strip()}'")
                        st.session_state.show_rename_dialog = False
                        st.rerun()
                    else:
                        st.error("⚠️ Введите имя графика")
            with col_b:
                if st.button("❌ Отмена", key="rename_cancel", use_container_width=True):
                    st.session_state.show_rename_dialog = False
                    st.rerun()

    st.markdown("</div>", unsafe_allow_html=True)

