import sympy as sp # заменяем на короткое название библиотеки чисто для удобства, используется в функции lambdify, которая переводит
# функция, которая лежит в дереве, в готовую функцию, которую python быстро считает.
from sympy.parsing.latex import parse_latex #преобразует латех формулу в sympy дерево для удобного хранения, в дальнейшем будет понятно, почему хранить в виде дерева удобною
import numpy as np #также, чисто для удобства, заменяем библиотеку на ее сокращение np


class SymPyFunction: # создаем базовый класс
    def __init__(self, formula_latex):
        self.formula_latex = formula_latex
        self.expr = parse_latex(formula_latex)
        self.symbols = list(self.expr.free_symbols)
        self.func_compiled = None

    def compile(self, symbol_order):  # компилирует sympy дерево в функцию, на вход получает один параметр - порядок переменных в функции, первый параметр обязателен для метода класса.
        self.func_compiled = sp.lambdify(symbol_order, self.expr, 'numpy')
        return self.func_compiled

    def evaluate(self, **kwargs): # вычисляет значение функции для заданных значений переменных, на вход получает **kwargs:dict - именованные аргументы, хранить удобно именно как именованные переменные,
        #потому, что могут функции с большим количеством переменных и удобно мочь различать разные перменные, короче просто удобно. Храним именованные аргументы с помощью словаря; в питоне это сделано
        #удобно, мы пишем просто **kwargs  такая штука принимает произвольное количество аргументов на вход и автоматически преобразует их в словарь. 
        if self.func_compiled is None:
            symbol_order = [sp.Symbol(k) for k in kwargs.keys()]
            self.compile(symbol_order)

        values = [kwargs[str(sym)] for sym in self.func_compiled.__code__.co_varnames[:len(kwargs)]]
        return self.func_compiled(*values)