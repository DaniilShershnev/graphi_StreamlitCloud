# Инструкции по компиляции научной работы

## Файлы

- **scientific_work_continuation.tex** - основной LaTeX документ с выводами
- **output/** - папка со всеми сгенерированными графиками

## Сгенерированные графики

### Фазовые портреты:
- `output/phase_portrait_general.svg` - общий случай системы (5)-(6)
- `output/phase_portrait_frenkel_A02.svg` - модель Френкеля, A=0.2
- `output/phase_portrait_frenkel_A05.svg` - модель Френкеля, A=0.5
- `output/phase_portrait_frenkel_A08.svg` - модель Френкеля, A=0.8

### Временные ряды:
- `output/timeseries_ic1.svg` - начальные условия s₀=0.5, w₀=0.3
- `output/timeseries_ic2.svg` - начальные условия s₀=1.0, w₀=0.5
- `output/timeseries_ic3.svg` - начальные условия s₀=1.5, w₀=0.7
- `output/timeseries_ic4.svg` - начальные условия s₀=0.3, w₀=0.4
- `output/timeseries_frenkel_A02.svg` - Френкель A=0.2
- `output/timeseries_frenkel_A05.svg` - Френкель A=0.5
- `output/timeseries_frenkel_A08.svg` - Френкель A=0.8

## Компиляция в PDF

### Вариант 1: Локальная компиляция (если установлен LaTeX)

```bash
cd D:/graphic
pdflatex scientific_work_continuation.tex
pdflatex scientific_work_continuation.tex  # Второй раз для корректных ссылок
```

### Вариант 2: Онлайн компилятор Overleaf

1. Зайти на https://www.overleaf.com
2. Создать новый проект "Upload Project"
3. Загрузить файл `scientific_work_continuation.tex`
4. Создать папку `output/` в проекте
5. Загрузить все SVG файлы из папки `output/` в эту папку
6. Нажать "Recompile" для генерации PDF

### Вариант 3: Онлайн компилятор LaTeX Base

1. Зайти на https://latexbase.com
2. Вставить содержимое файла `scientific_work_continuation.tex`
3. Загрузить SVG файлы через "Upload Files"
4. Нажать "Generate PDF"

## Важные замечания

1. **SVG файлы должны быть в папке output/** - убедитесь, что все графики находятся в правильной директории относительно .tex файла

2. **Кодировка UTF-8** - файл использует русский язык, убедитесь что редактор сохраняет в UTF-8

3. **Пакеты LaTeX** - документ требует следующие пакеты:
   - inputenc (UTF-8)
   - babel (russian)
   - amsmath, amssymb, amsthm
   - graphicx
   - float
   - geometry

4. **Два прохода компиляции** - для корректных ссылок на рисунки нужно скомпилировать дважды

## Параметры системы

В работе использованы следующие численные параметры:
- α = 2
- β = 1
- a = 0.1
- c = 0.3
- b = 1.0

Для модели Френкеля: g(s) = (1-A)(s-1)² + A
- A ∈ {0.2, 0.5, 0.8}

## Структура документа

1. Введение
2. Поиск положений равновесия
3. Линеаризация и якобиан системы
4. Модель Френкеля (МФ)
5. Фазовые портреты
6. Интегральные кривые
7. Заключение
