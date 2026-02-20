import sympy as sp
from sympy.parsing.latex import parse_latex
import numpy as np


class ODESystem:
    def __init__(self, equations_latex, variable_names):
        self.equations_latex = equations_latex
        self.variable_names = variable_names
        self.equations = [parse_latex(eq) for eq in equations_latex]

        self.variables = [sp.Symbol(name) for name in variable_names]

        all_symbols = set()
        for eq in self.equations:
            all_symbols.update(eq.free_symbols)

        self.params = []
        for sym in all_symbols:
            if sym not in self.variables and str(sym) != 't':
                self.params.append(sym)

        self.func_compiled = None

    def compile(self, param_values):
        t = sp.Symbol('t')

        substituted = []
        for eq in self.equations:
            expr = eq
            for param, value in zip(self.params, param_values):
                expr = expr.subs(param, value)
            substituted.append(expr)

        args = [t] + self.variables
        self.func_compiled = sp.lambdify(args, substituted, 'numpy')
        return self.func_compiled

    def right_hand_side(self, t, y, param_values):
        if self.func_compiled is None:
            self.compile(param_values)

        result = self.func_compiled(t, *y)
        return np.array(result)