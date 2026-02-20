# График - быстрая инструкция

**Проект:** `D:\graphic — clear version`

## Workflow
1. Создай YAML файл в `configs/имя.yaml` (используй Write tool)
2. Запусти: `python main.py --config configs/имя.yaml`
3. Результат в `output/имя.svg`

## 3 типа графиков

### 1. function - график f(x)
```yaml
type: function
curves:
  - formula: "x^2 + \\sin(x)"    # ВАЖНО: \\ (двойной слеш)
    x_range: [-10, 10]
    style: {color: "blue", linewidth: 1.5}
axes:
  xlim: [-10, 10]
  ylim: [-5, 5]
  xlabel: "x"
  ylabel: "y"
output: "func.svg"
```

### 2. ode_time - ОДУ от времени
```yaml
type: ode_time
curves:
  - equations: ["\\alpha*x - \\beta*x*y", "\\delta*x*y - \\gamma*y"]
    variable_names: [x, y]
    initial_conditions: [10, 5]
    params: {alpha: 1.5, beta: 0.1, gamma: 1.0, delta: 0.075}
    t_span: [0, 30]
    styles:    # styles - множественное число, список!
      - {color: "blue", linestyle: "-"}
      - {color: "red", linestyle: "--"}
axes:
  xlabel: "t"
  ylabel: "value"
output: "ode.svg"
```

### 3. phase_portrait - фазовый портрет
```yaml
type: phase_portrait
curves:
  - equations: ["y", "-\\sin(x)"]
    variable_names: [x, y]
    initial_conditions: [1, 0]
    t_span: [0, 50]
    var_indices: [0, 1]    # индексы с 0: [x, y] → x=0, y=1
    style: {color: "blue"} # style - единственное число!
vector_field:
  enabled: true
  density: 15
axes:
  xlabel: "x"
  ylabel: "y"
output: "phase.svg"
```

## LaTeX
```
\\sin(x) \\cos(x) \\exp(x) \\ln(x) \\sqrt(x)
\\alpha \\beta \\gamma \\delta \\omega \\theta
+  -  *  /  ^ (степень)
```

## Стили
- linestyle: `"-"` (сплошная), `"--"` (пунктир), `"-."` (штрих-пунктир), `":"` (точки)
- color: `"blue"` `"red"` `"green"` `"orange"` `"purple"` `"black"` `"gray"`

## Критично
1. LaTeX: ВСЕГДА `\\` (двойной слеш), не `\`
2. ode_time: `styles` (список)
3. phase_portrait: `style` (один dict)
4. Длины совпадают: equations = variable_names = initial_conditions = styles
