from core.base_plotter import GraphPlotter
from core.function_wrapper import SymPyFunction
from utils.validators import merge_params
import numpy as np


class FunctionPlotter(GraphPlotter):
    def __init__(self, global_params, dpi=300):
        super().__init__(dpi=dpi)
        self.global_params = global_params

    def add_curve_from_latex(self, formula_latex, params, x_range, style):
        func = SymPyFunction(formula_latex)

        merged_params = merge_params(self.global_params, params)

        x_values = np.linspace(x_range[0], x_range[1], merged_params.get('n_points', 1000))

        symbol_order = [s for s in func.symbols if str(s) == 'x']
        other_symbols = [s for s in func.symbols if str(s) != 'x']

        all_symbols = symbol_order + other_symbols
        func.compile(all_symbols)

        param_values = [merged_params[str(s)] for s in other_symbols]
        y_values = func.func_compiled(x_values, *param_values)

        self.add_curve(x_values, y_values, style)