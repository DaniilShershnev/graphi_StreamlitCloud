#!/usr/bin/env python3
"""
Script to create Excel file for time series analysis
"""
import pandas as pd
import os

# Data for time series - different initial conditions
data = {
    'output': [
        'timeseries_ic1.svg',
        'timeseries_ic2.svg',
        'timeseries_ic3.svg',
        'timeseries_ic4.svg',
        'timeseries_frenkel_A02.svg',
        'timeseries_frenkel_A05.svg',
        'timeseries_frenkel_A08.svg',
    ],
    's0': [0.5, 1.0, 1.5, 0.3, 0.8, 1.2, 1.0],
    'w0': [0.3, 0.5, 0.7, 0.4, 0.6, 0.5, 0.6],
    't_max': [50, 50, 50, 50, 80, 80, 80],
    'equation_1': [
        '0.1 * w^{1} - s * w^{(1-2)}',
        '0.1 * w^{1} - s * w^{(1-2)}',
        '0.1 * w^{1} - s * w^{(1-2)}',
        '0.1 * w^{1} - s * w^{(1-2)}',
        '0.1 * w^{1} - s * w^{(1-2)}',
        '0.1 * w^{1} - s * w^{(1-2)}',
        '0.1 * w^{1} - s * w^{(1-2)}',
    ],
    'equation_2': [
        '0.3 * (1 - w * (1 + 1.0 * (1 + s)))',
        '0.3 * (1 - w * (1 + 1.0 * (1 + s)))',
        '0.3 * (1 - w * (1 + 1.0 * (1 + s)))',
        '0.3 * (1 - w * (1 + 1.0 * (1 + s)))',
        '0.3 * (1 - w * (1 + 1.0 * (0.8 * (s-1)^2 + 0.2)))',
        '0.3 * (1 - w * (1 + 1.0 * (0.5 * (s-1)^2 + 0.5)))',
        '0.3 * (1 - w * (1 + 1.0 * (0.2 * (s-1)^2 + 0.8)))',
    ],
    'label': [
        's₀=0.5, w₀=0.3',
        's₀=1.0, w₀=0.5',
        's₀=1.5, w₀=0.7',
        's₀=0.3, w₀=0.4',
        'Frenkel A=0.2',
        'Frenkel A=0.5',
        'Frenkel A=0.8',
    ],
}

# Create DataFrame
df = pd.DataFrame(data)

# Save to Excel
output_path = 'D:/graphic/configs/scientific_work/timeseries_data.xlsx'
os.makedirs(os.path.dirname(output_path), exist_ok=True)
df.to_excel(output_path, index=False, sheet_name='Data')

print(f"Excel file created: {output_path}")
print(f"Total rows: {len(df)}")
