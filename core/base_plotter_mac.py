import matplotlib.pyplot as plt  # как будет видно ниже, очень удобно использовать сокращение переменных.
import numpy as np               # тоже сократим для красоты


# На всякий случай комментарий:
# перед переменными мы пишем self. так как мы ссылаемся на объект класса. В C++ указателем на объект класса было this->
# Espessialy for Gosha: в питоне нет строго разделения переменных на приватные и публичные

# ============================================================================
# ВЕРСИЯ ДЛЯ macOS: Изменён шрифт с 'Times New Roman' на 'DejaVu Serif'
# для совместимости с macOS. Все остальное идентично оригинальному файлу.
# ============================================================================

#GraphPlotter - это базовый класс, от которого наследуется(пока что) два класса: FunctionPlotter и ODEPlotter
class GraphPlotter:
    # Ниже def __init__(self): - это конструктор, им инициализируем переменные по умолчанию. В функции __init__ пишем self, self является указателем на создаваемый объект.
    def __init__(self, dpi=300):
        # ИЗМЕНЕНО ДЛЯ macOS: DejaVu Serif вместо Times New Roman
        plt.rcParams['font.family'] = 'DejaVu Serif'       # macOS-совместимый шрифт
        plt.rcParams['font.size'] = 14                     #указываем нужный размер шриафта.
        #Можно указывать разный размер текста для разных элементов:
        plt.rcParams['axes.labelsize'] = 42                #размер подписей осей (увеличен в 3 раза: 14 × 3 = 42)
        plt.rcParams['xtick.labelsize'] = 28               #разметка по оси ox (увеличен в 2 раза: 14 × 2 = 28)
        plt.rcParams['ytick.labelsize'] = 28               #разметка по оси oy (увеличен в 2 раза: 14 × 2 = 28)
        plt.rcParams['legend.fontsize'] = 14               #легенда
        self.fig, self.ax = plt.subplots(figsize=(8,8))   # соотношение сторон, по факту растяжение
        self.ax2 = None  # Вторая ось Y (правая), создается при необходимости
        self.curves = []
        self.dpi = dpi  # Сохраняем DPI для использования при сохранении

    def enable_dual_y_axis(self):
        """Создает вторую ось Y (правую) для отображения данных в другом масштабе"""
        if self.ax2 is None:
            self.ax2 = self.ax.twinx()
        return self.ax2

    def set_axes(self, xlim=None, ylim=None, xlabel='', ylabel='', grid=False, equal_aspect=False, spines=None,
                 grid_style=None, xticks=None, yticks=None, axis_labels_at_end=False,
                 dual_y_axis=False, ylim_right=None, ylabel_right='', yticks_right=None,
                 xticks_minor=None, yticks_minor=None, yticks_minor_right=None):
        # Создаем вторую ось, если требуется
        if dual_y_axis and self.ax2 is None:
            self.enable_dual_y_axis()

        # Настройка левой оси Y
        if xlim:
            self.ax.set_xlim(xlim)
        if ylim:
            self.ax.set_ylim(ylim)

        # Настройка правой оси Y
        if self.ax2 is not None and ylim_right:
            self.ax2.set_ylim(ylim_right)

        # Если нужно разместить подписи у концов осей
        if axis_labels_at_end:
            # Убираем стандартные подписи
            self.ax.set_xlabel('')
            self.ax.set_ylabel('')

            # Получаем пределы осей
            x_min, x_max = self.ax.get_xlim()
            y_min, y_max = self.ax.get_ylim()

            # Подпись оси X (справа от конца оси)
            if xlabel:
                self.ax.text(x_max, y_min, f' {xlabel}',
                           ha='left', va='top', fontsize=14)

            # Подпись оси Y (сверху от конца оси)
            if ylabel:
                self.ax.text(x_min, y_max, f' {ylabel}',
                           ha='left', va='bottom', fontsize=14)
        else:
            # Стандартные подписи по центру
            self.ax.set_xlabel(xlabel)
            self.ax.set_ylabel(ylabel)

            # Подпись правой оси Y
            if self.ax2 is not None and ylabel_right:
                self.ax2.set_ylabel(ylabel_right)

        # Настройка основных делений осей (major ticks)
        if xticks:
            self.ax.set_xticks(xticks)
        if yticks:
            self.ax.set_yticks(yticks)
        if self.ax2 is not None and yticks_right:
            self.ax2.set_yticks(yticks_right)

        # Настройка дополнительных делений осей БЕЗ подписей (minor ticks)
        if xticks_minor:
            self.ax.set_xticks(xticks_minor, minor=True)
        if yticks_minor:
            self.ax.set_yticks(yticks_minor, minor=True)
        if self.ax2 is not None and yticks_minor_right:
            self.ax2.set_yticks(yticks_minor_right, minor=True)

        # Настройка внешнего вида minor ticks (делаем короче major ticks)
        if xticks_minor or yticks_minor:
            self.ax.tick_params(which='minor', length=4, width=0.8)
        if self.ax2 is not None and yticks_minor_right:
            self.ax2.tick_params(which='minor', length=4, width=0.8)

        # Настройка границ (spines)
        if spines:
            for spine in ['top', 'right', 'bottom', 'left']:
                if spine in spines:
                    self.ax.spines[spine].set_visible(spines[spine])

        # Настройка сетки
        if grid:
            if grid_style:
                self.ax.grid(True, **grid_style)
            else:
                self.ax.grid(True, alpha=0.3)
        else:
            self.ax.grid(False)

        if equal_aspect:
            self.ax.set_aspect('equal')

    def set_title(self, title, fontsize=16, pad=20):
        """
        Устанавливает заголовок графика

        Параметры:
        - title: текст заголовка
        - fontsize: размер шрифта заголовка (по умолчанию 16)
        - pad: отступ от графика (по умолчанию 20)
        """
        self.ax.set_title(title, fontsize=fontsize, pad=pad)

    def add_curve(self, x, y, style, use_right_axis=False):
        """
        Добавляет кривую на график

        Параметры:
        - x, y: данные для построения
        - style: стиль линии (словарь с параметрами plot)
        - use_right_axis: если True, рисует на правой оси Y (требует dual_y_axis=True)
        """
        if use_right_axis and self.ax2 is not None:
            line, = self.ax2.plot(x, y, **style)
        else:
            line, = self.ax.plot(x, y, **style)
        self.curves.append(line)

    def add_arrows_to_curve(self, x, y, color='black', num_arrows=3, arrow_size=10):
        """
        Добавляет стрелки на кривую для показа направления движения

        Параметры:
        - x, y: данные кривой
        - color: цвет стрелок
        - num_arrows: количество стрелок
        - arrow_size: размер стрелок
        """
        import numpy as np

        # Выбираем равномерно распределенные точки для стрелок
        n = len(x)
        if n < 2:
            return

        # Индексы для стрелок (пропускаем начало и конец)
        indices = np.linspace(n // (num_arrows + 1), n - n // (num_arrows + 1), num_arrows, dtype=int)

        for i in indices:
            if i >= n - 1:
                continue

            # Направление стрелки
            dx = x[i + 1] - x[i]
            dy = y[i + 1] - y[i]

            # Нормализуем
            norm = np.sqrt(dx**2 + dy**2)
            if norm < 1e-10:
                continue

            self.ax.annotate('',
                xy=(x[i + 1], y[i + 1]),
                xytext=(x[i], y[i]),
                arrowprops=dict(
                    arrowstyle='->',
                    color=color,
                    lw=1.5,
                    mutation_scale=arrow_size
                )
            )

    def add_horizontal_line(self, y, axis='left', color='black', linestyle='-', linewidth=1, label=None, alpha=1.0):
        """
        Добавляет горизонтальную линию (например, для асимптоты)

        Параметры:
        - y: значение на оси Y, где провести линию
        - axis: 'left' или 'right' - на какой оси Y рисовать (для dual_y_axis)
        - color: цвет линии
        - linestyle: стиль линии ('-', '--', '-.', ':')
        - linewidth: толщина линии
        - label: подпись для легенды (опционально)
        - alpha: прозрачность (0-1)
        """
        if axis == 'right' and self.ax2 is not None:
            self.ax2.axhline(y=y, color=color, linestyle=linestyle, linewidth=linewidth, label=label, alpha=alpha)
        else:
            self.ax.axhline(y=y, color=color, linestyle=linestyle, linewidth=linewidth, label=label, alpha=alpha)

    def add_equilibrium_label(self, y, text, axis='left', x_position='right', color='black', fontsize=12,
                             bbox_style=None, offset=(5, 0)):
        """
        Добавляет текстовую метку для равновесия/асимптоты

        Параметры:
        - y: значение Y где разместить метку
        - text: текст метки (например, "s*=405.2")
        - axis: 'left' или 'right' - какой оси соответствует
        - x_position: 'left', 'right' или 'center' - где по горизонтали разместить
        - color: цвет текста
        - fontsize: размер шрифта
        - bbox_style: стиль рамки вокруг текста (dict для bbox), например:
                     {'boxstyle': 'round', 'facecolor': 'white', 'alpha': 0.8}
        - offset: смещение метки от края в пикселях (dx, dy)
        """
        # Выбираем нужную ось
        target_ax = self.ax2 if (axis == 'right' and self.ax2 is not None) else self.ax

        # Получаем пределы оси X
        xlim = target_ax.get_xlim()

        # Определяем позицию по X
        if x_position == 'left':
            x = xlim[0]
            ha = 'left'
        elif x_position == 'right':
            x = xlim[1]
            ha = 'right'
        else:  # center
            x = (xlim[0] + xlim[1]) / 2
            ha = 'center'

        # Добавляем текстовую метку
        target_ax.text(
            x, y, text,
            horizontalalignment=ha,
            verticalalignment='center',
            color=color,
            fontsize=fontsize,
            bbox=bbox_style if bbox_style else None,
            transform=target_ax.get_yaxis_transform() if x_position in ['left', 'right'] else None
        )

    def add_vertical_line(self, x, color='black', linestyle='-', linewidth=1, label=None):
        """
        Добавляет вертикальную линию (например, для асимптоты)

        Параметры:
        - x: значение на оси X, где провести линию
        - color: цвет линии
        - linestyle: стиль линии ('-', '--', '-.', ':')
        - linewidth: толщина линии
        - label: подпись для легенды (опционально)
        """
        self.ax.axvline(x=x, color=color, linestyle=linestyle, linewidth=linewidth, label=label)

    def save(self, filename):
        # Определяем формат по расширению файла
        import os
        ext = os.path.splitext(filename)[1].lower()

        # ВАЖНО: Удаляем существующий файл если он есть
        # Это решает проблему с невозможностью перезаписи некоторых файлов (особенно начинающихся с цифр)
        if os.path.exists(filename):
            try:
                os.remove(filename)
            except Exception as e:
                print(f"Warning: Couldn't delete existing file {filename}: {e}")

        if ext == '.png':
            # Для PNG используем DPI из конфига (по умолчанию 300)
            # Без bbox_inches='tight' для строго квадратных изображений
            self.fig.savefig(filename, format='png', dpi=self.dpi)
        else:
            # По умолчанию SVG
            self.fig.savefig(filename, format='svg')

        plt.close(self.fig)
        #поямнения к формуле выше:


        # Чтобы сохранять абсолютно все точки, которые считаются(о чем речь - см файл), нужно:
        #import matplotlib as mpl
        #mpl.rcParams['path.simplify'] = False  # <-- Отключить упрощение
        #mpl.rcParams['path.simplify_threshold'] = 0.0  # <-- Порог = 0

        #self.fig.savefig(filename, format='svg', bbox_inches='tight')
        #plt.close(self.fig)

    def clear(self):
        self.ax.clear()
        self.curves = []
