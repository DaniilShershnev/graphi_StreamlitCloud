#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Модуль для численного поиска положений равновесия динамических систем ОДУ.

Равновесие (стационарная точка) - это состояние (s*, w*), где:
    ds/dt = 0
    dw/dt = 0

Модуль использует два подхода:
1. Численное интегрирование на большом временном интервале
2. Уточнение через scipy.optimize.fsolve
"""

import numpy as np
from scipy.integrate import solve_ivp
from scipy.optimize import fsolve
from typing import Dict, Tuple, Optional, Callable
import warnings


class EquilibriumFinder:
    """
    Класс для поиска равновесий системы ОДУ.
    """

    def __init__(self, ode_func: Callable, convergence_threshold: float = 1e-6):
        """
        Инициализация поискового модуля.

        Параметры:
        ----------
        ode_func : callable
            Функция правых частей ОДУ с сигнатурой: f(t, y, params) -> dy/dt
        convergence_threshold : float
            Порог для проверки сходимости (максимальное |dy/dt|)
        """
        self.ode_func = ode_func
        self.convergence_threshold = convergence_threshold

    def find_by_integration(
        self,
        y0: np.ndarray,
        params: Dict,
        t_max: float = 1000.0,
        method: str = 'LSODA'
    ) -> Tuple[np.ndarray, bool, Dict]:
        """
        Поиск равновесия численным интегрированием до большого времени.

        Параметры:
        ----------
        y0 : np.ndarray
            Начальные условия [s0, w0]
        params : dict
            Параметры системы
        t_max : float
            Время интегрирования (чем больше, тем точнее, но медленнее)
        method : str
            Метод интегрирования (LSODA, Radau, BDF)

        Возвращает:
        -----------
        equilibrium : np.ndarray
            Найденное равновесие [s*, w*]
        converged : bool
            True если система сошлась к равновесию
        info : dict
            Дополнительная информация (производные, время сходимости и т.д.)
        """
        try:
            # Интегрируем систему
            sol = solve_ivp(
                fun=lambda t, y: self.ode_func(t, y, params),
                t_span=[0, t_max],
                y0=y0,
                method=method,
                dense_output=False,
                rtol=1e-8,
                atol=1e-10
            )

            if not sol.success:
                return y0, False, {'error': 'Integration failed', 'message': sol.message}

            # Берем последнее значение как приближение к равновесию
            y_final = sol.y[:, -1]

            # Вычисляем производные в конечной точке
            derivatives = self.ode_func(sol.t[-1], y_final, params)
            max_derivative = np.max(np.abs(derivatives))

            # Проверяем сходимость
            converged = max_derivative < self.convergence_threshold

            info = {
                'derivatives': derivatives,
                'max_derivative': max_derivative,
                't_final': sol.t[-1],
                'converged': converged,
                'trajectory_length': len(sol.t)
            }

            return y_final, converged, info

        except Exception as e:
            return y0, False, {'error': str(e)}

    def refine_by_optimization(
        self,
        y_guess: np.ndarray,
        params: Dict,
        method: str = 'hybr'
    ) -> Tuple[np.ndarray, bool, Dict]:
        """
        Уточнение равновесия через решение системы f(y) = 0.

        Параметры:
        ----------
        y_guess : np.ndarray
            Начальное приближение [s_guess, w_guess]
        params : dict
            Параметры системы
        method : str
            Метод оптимизации ('hybr', 'lm', 'broyden1')

        Возвращает:
        -----------
        equilibrium : np.ndarray
            Уточненное равновесие [s*, w*]
        success : bool
            True если оптимизация успешна
        info : dict
            Информация об оптимизации
        """
        try:
            # Определяем систему уравнений f(y) = 0
            def equations(y):
                return self.ode_func(0, y, params)

            # Решаем систему
            with warnings.catch_warnings():
                warnings.simplefilter("ignore")

                if method == 'fsolve':
                    solution, infodict, ier, msg = fsolve(
                        equations,
                        y_guess,
                        full_output=True
                    )
                    success = (ier == 1)
                else:
                    from scipy.optimize import root
                    result = root(equations, y_guess, method=method)
                    solution = result.x
                    success = result.success
                    msg = result.message

            # Проверяем что решение действительно обнуляет производные
            residual = equations(solution)
            max_residual = np.max(np.abs(residual))

            info = {
                'residual': residual,
                'max_residual': max_residual,
                'method': method,
                'message': msg if isinstance(msg, str) else str(msg)
            }

            return solution, success, info

        except Exception as e:
            return y_guess, False, {'error': str(e)}

    def find_equilibrium(
        self,
        y0: np.ndarray,
        params: Dict,
        t_max: float = 1000.0,
        refine: bool = True
    ) -> Dict:
        """
        Полный поиск равновесия: интегрирование + уточнение.

        Параметры:
        ----------
        y0 : np.ndarray
            Начальные условия [s0, w0]
        params : dict
            Параметры системы
        t_max : float
            Время интегрирования
        refine : bool
            Уточнять ли результат через оптимизацию

        Возвращает:
        -----------
        result : dict
            Полная информация о найденном равновесии:
            {
                'equilibrium': [s*, w*],
                'converged': bool,
                'integration_info': dict,
                'refinement_info': dict (если refine=True)
            }
        """
        # Шаг 1: Численное интегрирование
        y_approx, converged_int, info_int = self.find_by_integration(
            y0, params, t_max
        )

        result = {
            'equilibrium': y_approx,
            'converged': converged_int,
            'integration_info': info_int,
            'method': 'integration'
        }

        # Шаг 2: Уточнение через оптимизацию (опционально)
        if refine and converged_int:
            y_refined, success_opt, info_opt = self.refine_by_optimization(
                y_approx, params
            )

            if success_opt:
                result['equilibrium'] = y_refined
                result['refinement_info'] = info_opt
                result['method'] = 'integration + optimization'

        return result

    def analyze_stability(
        self,
        equilibrium: np.ndarray,
        params: Dict
    ) -> Dict:
        """
        Анализ устойчивости и типа равновесия.

        Вычисляет матрицу Якоби численно, находит собственные значения
        и определяет тип равновесия (узел, фокус, седло) и устойчивость.

        Параметры:
        ----------
        equilibrium : np.ndarray
            Точка равновесия [s*, w*]
        params : dict
            Параметры системы

        Возвращает:
        -----------
        result : dict
            {
                'eigenvalues': собственные значения,
                'stability': 'Устойчивое'|'Неустойчивое'|'Седло',
                'type': 'Узел'|'Фокус'|'Седло'|'Центр',
                'real_parts': вещественные части собственных значений,
                'imag_parts': мнимые части собственных значений
            }
        """
        epsilon = 1e-8
        n = len(equilibrium)
        jacobian = np.zeros((n, n))

        # Численно вычисляем матрицу Якоби: J_ij = ∂f_i/∂y_j
        f0 = self.ode_func(0, equilibrium, params)

        for j in range(n):
            y_perturbed = equilibrium.copy()
            y_perturbed[j] += epsilon
            f_perturbed = self.ode_func(0, y_perturbed, params)
            jacobian[:, j] = (f_perturbed - f0) / epsilon

        # Вычисляем собственные значения
        eigenvalues = np.linalg.eigvals(jacobian)

        # Анализируем вещественные и мнимые части
        real_parts = np.real(eigenvalues)
        imag_parts = np.imag(eigenvalues)

        # Определяем устойчивость
        if np.all(real_parts < -1e-10):  # все λ < 0
            stability = "Устойчивое"
        elif np.all(real_parts > 1e-10):  # все λ > 0
            stability = "Неустойчивое"
        elif np.any(real_parts > 1e-10) and np.any(real_parts < -1e-10):  # разные знаки
            stability = "Седло (неустойчивое)"
        else:  # близко к нулю
            stability = "Нейтральное"

        # Определяем тип равновесия для 2D систем
        if n == 2:
            # Проверяем наличие комплексных собственных значений
            has_complex = np.any(np.abs(imag_parts) > 1e-10)

            if stability == "Седло (неустойчивое)":
                eq_type = "Седло"
            elif has_complex:
                # Фокус (спираль)
                if np.all(real_parts < -1e-10):
                    eq_type = "Устойчивый фокус"
                elif np.all(real_parts > 1e-10):
                    eq_type = "Неустойчивый фокус"
                elif np.allclose(real_parts, 0, atol=1e-10):
                    eq_type = "Центр"
                else:
                    eq_type = "Фокус"
            else:
                # Узел (вещественные собственные значения)
                if np.all(real_parts < -1e-10):
                    eq_type = "Устойчивый узел"
                elif np.all(real_parts > 1e-10):
                    eq_type = "Неустойчивый узел"
                else:
                    eq_type = "Узел"
        else:
            eq_type = "N/A (не 2D система)"

        return {
            'eigenvalues': eigenvalues,
            'real_parts': real_parts,
            'imag_parts': imag_parts,
            'stability': stability,
            'type': eq_type,
            'jacobian': jacobian
        }


def find_equilibrium_simple(
    ode_func: Callable,
    y0: np.ndarray,
    params: Dict,
    t_max: float = 1000.0
) -> Tuple[float, float]:
    """
    Упрощенная функция для быстрого поиска равновесия.

    Параметры:
    ----------
    ode_func : callable
        Функция правых частей ОДУ
    y0 : array
        Начальные условия [s0, w0]
    params : dict
        Параметры системы
    t_max : float
        Время интегрирования

    Возвращает:
    -----------
    s_star : float
        Стационарное значение s
    w_star : float
        Стационарное значение w
    """
    finder = EquilibriumFinder(ode_func)
    result = finder.find_equilibrium(y0, params, t_max, refine=False)

    equilibrium = result['equilibrium']
    return equilibrium[0], equilibrium[1]
