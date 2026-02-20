import pandas as pd

df = pd.read_excel('excel/pic9a_power_exp.xlsx', sheet_name='Data')

# Найдем проблемные строки
problem_outputs = [
    '2pic11_power_power_a_10.png',
    '2pic11_power_power_a_70.png',
    '2pic11_power_exp_a_1000.png'
]

for output_name in problem_outputs:
    print(f"\n{'='*60}")
    print(f"Analyzing: {output_name}")
    print(f"{'='*60}")

    rows = df[df['output'] == output_name]
    print(f"Found {len(rows)} rows with this output")

    if len(rows) > 0:
        # Показываем первую строку
        first_row = rows.iloc[0]
        print(f"\nFirst row (index {first_row.name}):")
        print(f"  output: {repr(first_row['output'])}")
        print(f"  graph_type: {first_row.get('graph_type', 'N/A')}")
        print(f"  a: {first_row.get('a', 'N/A')}")

        # Проверяем все колонки на NaN или странные значения
        print(f"\nAll columns for this row:")
        for col in df.columns:
            val = first_row[col]
            if pd.isna(val):
                print(f"  {col}: <NaN>")
            else:
                print(f"  {col}: {repr(val)}")
