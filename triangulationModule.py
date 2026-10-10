#!/usr/bin/env python3.13
"""
Модуль триангуляции для определения координат Wi-Fi роутера
на основе измерений мощности сигнала в фиксированных точках.
"""

import math
from typing import List, Tuple, Dict
from dataclasses import dataclass
from scipy.optimize import minimize


@dataclass
class MeasurementPoint:
    """Точка измерения с координатами и мощностью сигнала"""
    name: str
    x: float  # координата X в метрах
    y: float  # координата Y в метрах
    signal_dbmv: float  # мощность сигнала в dbmV


class WiFiTriangulation:
    """
    Класс для выполнения триангуляции Wi-Fi роутера.

    Модель преобразования мощности сигнала в расстояние основана на
    логарифмической модели потерь пути (Log Distance Path Loss Model).
    """

    # Эталонная мощность на расстоянии 1м (примерное значение для Wi-Fi)
    REFERENCE_POWER_DBM = -40  # dbmV на расстоянии 1м

    # Показатель затухания (path loss exponent) для разных сценариев
    # Используем значение 2.0 для свободного пространства, 
    # 3-4 для помещений с препятствиями
    PATH_LOSS_EXPONENT = 2.5

    def __init__(self):
        """Инициализация модуля триангуляции"""
        pass

    def signal_to_distance(self, signal_dbmv: float) -> float:
        """
        Преобразует мощность сигнала (dbmV) в расстояние (метры).

        Использует логарифмическую модель потерь пути:
        P(d) = P0 - 10 * n * log10(d/d0)
        где:
            P(d) - мощность на расстоянии d
            P0 - эталонная мощность
            n - показатель затухания
            d0 - эталонное расстояние (1м)

        Args:
            signal_dbmv: Мощность сигнала в dbmV

        Returns:
            Расстояние в метрах
        """
        # Обратная формула для расчета расстояния
        # d = 10 ^ ((P0 - P(d)) / (10 * n))
        power_diff = self.REFERENCE_POWER_DBM - signal_dbmv
        distance = 10 ** (power_diff / (10 * self.PATH_LOSS_EXPONENT))

        return max(distance, 0.1)  # минимальное расстояние 0.1м

    def get_distance_estimate(self, signal_dbmv: float) -> Tuple[str, float]:
        """
        Возвращает описание и оценку расстояния на основе мощности сигнала.

        Args:
            signal_dbmv: Мощность сигнала в dbmV

        Returns:
            Кортеж (описание, расстояние в метрах)
        """
        distance = self.signal_to_distance(signal_dbmv)

        if -40 <= signal_dbmv <= -30:
            description = "Вплотную к роутеру"
        elif -60 <= signal_dbmv <= -50:
            description = "В той же комнате или за тонкой стеной"
        elif -70 <= signal_dbmv <= -65:
            description = "На приличном расстоянии или за парой стен"
        elif -90 <= signal_dbmv <= -80:
            description = "Очень далеко или за толстой бетонной стеной"
        else:
            description = "Неизвестная зона покрытия"

        return description, distance

    def calculate_distances(self, 
                          measurement_points: List[MeasurementPoint]) -> Dict[str, float]:
        """
        Вычисляет расстояния от каждой точки измерения до роутера.

        Args:
            measurement_points: Список точек измерения с координатами и сигналом

        Returns:
            Словарь с расстояниями для каждой точки
        """
        distances = {}

        for point in measurement_points:
            distance = self.signal_to_distance(point.signal_dbmv)
            distances[point.name] = distance
            description, _ = self.get_distance_estimate(point.signal_dbmv)
            print(f"{point.name}: {point.signal_dbmv} dbmV -> {distance:.2f}м ({description})")

        return distances

    def triangulate(self, 
                   measurement_points: List[MeasurementPoint],
                   initial_guess: Tuple[float, float] = None) -> Tuple[float, float]:
        """
        Определяет координаты Wi-Fi роутера методом триангуляции.

        Использует метод минимизации ошибки расстояний от предполагаемого
        положения роутера до каждой точки измерения.

        Args:
            measurement_points: Список точек измерения
            initial_guess: Начальное предположение о координатах (x, y).
                          Если не указано, вычисляется как центроид точек.

        Returns:
            Кортеж (x, y) координат роутера
        """
        if len(measurement_points) < 2:
            raise ValueError("Необходимо минимум 2 точки измерения")

        # Начальное предположение - центроид всех точек измерения
        if initial_guess is None:
            avg_x = sum(p.x for p in measurement_points) / len(measurement_points)
            avg_y = sum(p.y for p in measurement_points) / len(measurement_points)
            initial_guess = (avg_x, avg_y)

        # Вычисляем расстояния от каждой точки до роутера
        distances = {}
        for point in measurement_points:
            distances[point.name] = self.signal_to_distance(point.signal_dbmv)

        # Функция для минимизации - сумма квадратов ошибок расстояний
        def objective(router_coords):
            """Вычисляет сумму квадратов разностей расчетных и измеренных расстояний"""
            router_x, router_y = router_coords
            error = 0

            for point in measurement_points:
                # Евклидово расстояние от точки до предполагаемого положения роутера
                calc_distance = math.sqrt((point.x - router_x)**2 + 
                                         (point.y - router_y)**2)

                # Расстояние, вычисленное из мощности сигнала
                measured_distance = distances[point.name]

                # Квадрат ошибки
                error += (calc_distance - measured_distance)**2

            return error

        # Методы оптимизации можно использовать разные; используем Nelder-Mead
        result = minimize(objective, initial_guess, method='Nelder-Mead',
                         options={'xatol': 1e-4, 'fatol': 1e-4})

        router_x, router_y = result.x

        # Выводим статистику
        final_error = result.fun
        print(f"\nРезультаты триангуляции:")
        print(f"Координаты роутера: ({router_x:.2f}, {router_y:.2f})")
        print(f"Ошибка оптимизации: {final_error:.4f}")

        return router_x, router_y

    def validate_triangulation(self, 
                              measurement_points: List[MeasurementPoint],
                              router_coords: Tuple[float, float]) -> None:
        """
        Проверяет качество триангуляции, сравнивая расчетные и измеренные расстояния.

        Args:
            measurement_points: Список точек измерения
            router_coords: Координаты найденного роутера
        """
        router_x, router_y = router_coords

        print("\nПроверка точности триангуляции:")
        print("-" * 70)
        print(f"{'Точка':<8} {'X':<10} {'Y':<10} {'dbmV':<10} {'Расчет,м':<12} {'Реальн,м':<12} {'Ошибка':<10}")
        print("-" * 70)

        total_error = 0

        for point in measurement_points:
            # Реальное расстояние от точки до найденного роутера
            real_distance = math.sqrt((point.x - router_x)**2 + 
                                     (point.y - router_y)**2)

            # Расстояние, вычисленное из мощности сигнала
            calculated_distance = self.signal_to_distance(point.signal_dbmv)

            error = abs(real_distance - calculated_distance)
            total_error += error

            print(f"{point.name:<8} {point.x:<10.2f} {point.y:<10.2f} "
                  f"{point.signal_dbmv:<10.1f} {calculated_distance:<12.2f} "
                  f"{real_distance:<12.2f} {error:<10.2f}")

        avg_error = total_error / len(measurement_points)
        print("-" * 70)
        print(f"Средняя ошибка: {avg_error:.2f}м")


def main():
    """Пример использования модуля триангуляции"""

    # Создаем объект триангуляции
    triangulation = WiFiTriangulation()

    # Точки измерения из диаграммы
    measurement_points = [
        MeasurementPoint("T1", x=50, y=30, signal_dbmv=-65),
        MeasurementPoint("T2", x=50, y=30, signal_dbmv=-40),
        MeasurementPoint("T3", x=30, y=30, signal_dbmv=-65),
        MeasurementPoint("T4", x=20, y=30, signal_dbmv=-80),
        MeasurementPoint("T5", x=23, y=40, signal_dbmv=-80),
        MeasurementPoint("T6", x=23, y=40, signal_dbmv=-50),
        MeasurementPoint("T7", x=45, y=50, signal_dbmv=-90),
    ]

    print("=" * 70)
    print("МОДУЛЬ ТРИАНГУЛЯЦИИ Wi-Fi РОУТЕРА")
    print("=" * 70)

    # Шаг 1: Вычисление расстояний
    print("\n1. Преобразование мощности сигнала в расстояния:")
    print("-" * 70)
    distances = triangulation.calculate_distances(measurement_points)

    # Шаг 2: Триангуляция
    print("\n2. Выполнение триангуляции...\n")
    router_x, router_y = triangulation.triangulate(measurement_points)

    # Шаг 3: Проверка точности
    triangulation.validate_triangulation(measurement_points, (router_x, router_y))

    print("\n" + "=" * 70)
    print(f"НАЙДЕНО ПОЛОЖЕНИЕ РОУТЕРА: ({router_x:.2f}, {router_y:.2f})")
    print("=" * 70)


if __name__ == "__main__":
    main()
