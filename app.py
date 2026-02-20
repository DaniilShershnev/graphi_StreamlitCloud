import streamlit as st
import sys
import os
import tempfile

# Настройка путей
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from core.function_plotter import FunctionPlotter
from core.ode_plotter import ODEPlotter
import params_global

st.set_page_config(page_title="График Builder", layout="wide")

st.title("📊 Построение графиков для курсовой")
st.markdown("**Проект:** Построение математических графиков, ОДУ и фазовых портретов")

# Выбор типа графика
plot_type = st.selectbox(
    "Тип графика",
    ["function", "ode_time", "phase_portrait"],
    format_func=lambda x: {
        "function": "Функция f(x)",
        "ode_time": "ОДУ - временные ряды",
        "phase_portrait": "Фазовый портрет"
    }[x]
)

st.markdown("---")

# ========== FUNCTION ==========
if plot_type == "function":
    st.header("График функции")

    col1, col2 = st.columns(2)

    with col1:
        formula = st.text_input(
            "Формула LaTeX (используйте двойной слеш \\\\)",
            value="x^2 + \\\\sin(x)",
            help="Примеры: x^2, \\\\exp(-x^2), \\\\sin(x)"
        )

        x_min = st.number_input("x min", value=-10.0, step=0.1)
        x_max = st.number_input("x max", value=10.0, step=0.1)

        color = st.selectbox("Цвет", ["blue", "red", "green", "orange", "purple", "black"])
        linewidth = st.slider("Толщина линии", 0.5, 3.0, 1.5, 0.1)

    with col2:
        xlabel = st.text_input("Подпись оси X", value="x")
        ylabel = st.text_input("Подпись оси Y", value="f(x)")

        ylim_auto = st.checkbox("Автоматические пределы по Y", value=True)
        if not ylim_auto:
            y_min = st.number_input("y min", value=-5.0, step=0.1)
            y_max = st.number_input("y max", value=5.0, step=0.1)

        grid = st.checkbox("Показать сетку", value=True)

    if st.button("📈 Построить график", type="primary"):
        try:
            plotter = FunctionPlotter(vars(params_global))
            plotter.add_curve_from_latex(
                formula,
                {},
                [x_min, x_max],
                {"color": color, "linewidth": linewidth}
            )

            ylim = None if ylim_auto else [y_min, y_max]
            plotter.set_axes(
                xlim=[x_min, x_max],
                ylim=ylim,
                xlabel=xlabel,
                ylabel=ylabel,
                grid=grid
            )

            # Сохраняем во временный файл
            with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                plotter.save(tmp.name)
                st.image(tmp.name)

                # Кнопка скачивания
                with open(tmp.name, 'rb') as f:
                    st.download_button(
                        "💾 Скачать SVG",
                        f.read(),
                        file_name="function.svg",
                        mime="image/svg+xml"
                    )
                os.unlink(tmp.name)

            st.success("✅ График успешно построен!")

        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

# ========== ODE TIME ==========
elif plot_type == "ode_time":
    st.header("ОДУ - временные ряды")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Система уравнений")

        num_vars = st.number_input("Количество переменных", 2, 5, 2, 1)

        equations = []
        variable_names = []
        initial_conditions = []
        colors = []
        linestyles = []

        for i in range(num_vars):
            st.markdown(f"**Переменная {i+1}:**")
            var_name = st.text_input(f"Имя переменной {i+1}", value=chr(120+i), key=f"var_{i}")
            variable_names.append(var_name)

            eq = st.text_input(
                f"Уравнение d{var_name}/dt =",
                value="-x" if i == 0 else "x - y",
                key=f"eq_{i}",
                help="Используйте двойной слеш: \\\\sin, \\\\exp, \\\\alpha"
            )
            equations.append(eq)

            ic = st.number_input(f"Начальное условие {var_name}(0)", value=float(i+1), key=f"ic_{i}")
            initial_conditions.append(ic)

            col_a, col_b = st.columns(2)
            with col_a:
                color = st.selectbox(f"Цвет {var_name}",
                                    ["blue", "red", "green", "orange", "purple"],
                                    key=f"col_{i}")
                colors.append(color)
            with col_b:
                linestyle = st.selectbox(f"Стиль {var_name}",
                                        ["-", "--", "-.", ":"],
                                        key=f"ls_{i}")
                linestyles.append(linestyle)

    with col2:
        st.subheader("Параметры")

        t_start = st.number_input("t начало", value=0.0, step=0.1)
        t_end = st.number_input("t конец", value=10.0, step=0.1)

        st.markdown("**Параметры системы:**")
        param_text = st.text_area(
            "Параметры (формат: a=1.5, b=0.1)",
            value="",
            help="Пример: alpha=1.5, beta=0.1, gamma=1.0"
        )

        # Парсим параметры
        params = {}
        if param_text.strip():
            for item in param_text.split(','):
                if '=' in item:
                    key, val = item.split('=')
                    params[key.strip()] = float(val.strip())

        xlabel = st.text_input("Подпись оси X", value="t", key="ode_xlabel")
        ylabel = st.text_input("Подпись оси Y", value="значение", key="ode_ylabel")
        grid = st.checkbox("Показать сетку", value=True, key="ode_grid")

    if st.button("📈 Построить ОДУ", type="primary"):
        try:
            plotter = ODEPlotter(vars(params_global))

            styles = [
                {"color": colors[i], "linestyle": linestyles[i], "linewidth": 1.5}
                for i in range(num_vars)
            ]

            plotter.solve_and_plot_time(
                equations,
                variable_names,
                initial_conditions,
                params,
                [t_start, t_end],
                styles
            )

            plotter.set_axes(
                xlabel=xlabel,
                ylabel=ylabel,
                grid=grid
            )

            with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                plotter.save(tmp.name)
                st.image(tmp.name)

                with open(tmp.name, 'rb') as f:
                    st.download_button(
                        "💾 Скачать SVG",
                        f.read(),
                        file_name="ode_time.svg",
                        mime="image/svg+xml"
                    )
                os.unlink(tmp.name)

            st.success("✅ График ОДУ успешно построен!")

        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

# ========== PHASE PORTRAIT ==========
else:  # phase_portrait
    st.header("Фазовый портрет")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Система уравнений")

        var1 = st.text_input("Переменная 1", value="x", key="pp_var1")
        eq1 = st.text_input(
            f"d{var1}/dt =",
            value="y",
            key="pp_eq1",
            help="Используйте двойной слеш: \\\\sin, \\\\exp"
        )
        ic1 = st.number_input(f"{var1}(0)", value=1.0, key="pp_ic1")

        var2 = st.text_input("Переменная 2", value="y", key="pp_var2")
        eq2 = st.text_input(
            f"d{var2}/dt =",
            value="-\\\\sin(x)",
            key="pp_eq2"
        )
        ic2 = st.number_input(f"{var2}(0)", value=0.0, key="pp_ic2")

        t_end = st.number_input("Время интегрирования", value=50.0, step=1.0, key="pp_tend")

        st.markdown("**Параметры:**")
        param_text = st.text_area(
            "Параметры (формат: a=1, b=2)",
            value="",
            key="pp_params"
        )

        params = {}
        if param_text.strip():
            for item in param_text.split(','):
                if '=' in item:
                    key, val = item.split('=')
                    params[key.strip()] = float(val.strip())

    with col2:
        st.subheader("Настройки графика")

        color = st.selectbox("Цвет траектории", ["blue", "red", "green", "orange", "purple"], key="pp_color")
        linewidth = st.slider("Толщина линии", 0.5, 3.0, 1.0, 0.1, key="pp_lw")

        xlabel = st.text_input("Подпись оси X", value=var1, key="pp_xlabel")
        ylabel = st.text_input("Подпись оси Y", value=var2, key="pp_ylabel")

        show_vector = st.checkbox("Показать векторное поле", value=True)

        if show_vector:
            density = st.slider("Плотность векторов", 5, 30, 15, 1)
            vector_color = st.selectbox("Цвет векторов", ["gray", "black", "blue"], key="pp_vcolor")
            alpha = st.slider("Прозрачность векторов", 0.1, 1.0, 0.5, 0.1)

    if st.button("📈 Построить фазовый портрет", type="primary"):
        try:
            plotter = ODEPlotter(vars(params_global))

            if show_vector:
                plotter.add_vector_field(
                    [eq1, eq2],
                    [var1, var2],
                    params,
                    [0, 1],
                    {
                        "density": density,
                        "color": vector_color,
                        "alpha": alpha,
                        "scale": 20,
                        "width": 0.002
                    }
                )

            plotter.solve_and_plot_phase(
                [eq1, eq2],
                [var1, var2],
                [ic1, ic2],
                params,
                [0, t_end],
                [0, 1],
                {"color": color, "linewidth": linewidth}
            )

            plotter.set_axes(
                xlabel=xlabel,
                ylabel=ylabel,
                grid=True
            )

            with tempfile.NamedTemporaryFile(delete=False, suffix='.svg') as tmp:
                plotter.save(tmp.name)
                st.image(tmp.name)

                with open(tmp.name, 'rb') as f:
                    st.download_button(
                        "💾 Скачать SVG",
                        f.read(),
                        file_name="phase_portrait.svg",
                        mime="image/svg+xml"
                    )
                os.unlink(tmp.name)

            st.success("✅ Фазовый портрет успешно построен!")

        except Exception as e:
            st.error(f"❌ Ошибка: {str(e)}")

# Футер
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: gray; font-size: 0.8em;'>
    Проект для курсовой работы | Построение графиков через Python
    </div>
    """,
    unsafe_allow_html=True
)
