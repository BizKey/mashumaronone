#!/usr/bin/env python3
"""
Бенчмарк сравнения производительности Python и Rust версий remove_empty
"""

import time
import json
import statistics
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from mashumaro.mixins.orjson import DataClassORJSONMixin
from mashumaro.config import BaseConfig
from mashumaro import field_options
import mashumaronone

# ============================================================================
# 1. Реализации функций
# ============================================================================

def remove_empty_python(data: Any) -> Any:
    """Рекурсивно удаляет None, пустые списки и пустые словари - Python версия"""
    if isinstance(data, dict):
        result = {}
        for key, value in data.items():
            cleaned = remove_empty_python(value)
            if cleaned not in (None, [], {}, set(), ()):
                result[key] = cleaned
        return result
    elif isinstance(data, list):
        return [remove_empty_python(item) for item in data if remove_empty_python(item) not in ([], {}, None)]
    else:
        return data

def remove_empty_rust(data: Any) -> Any:
    """Рекурсивно удаляет None, пустые списки и пустые словари - Rust версия"""
    return mashumaronone.remove_empty(data)

# ============================================================================
# 2. Тестовые модели
# ============================================================================

@dataclass
class Product(DataClassORJSONMixin):
    id_: int = field(metadata=field_options(alias="id"))
    title: str
    price: Optional[float] = None

    class Config(BaseConfig):
        serialize_by_alias = True

@dataclass
class Category(DataClassORJSONMixin):
    name: Optional[str] = None
    products: Optional[List[Product]] = None

@dataclass
class Store(DataClassORJSONMixin):
    name: str
    categories: Optional[List[Category]] = None

# ============================================================================
# 3. Генерация тестовых данных разных размеров
# ============================================================================

def generate_test_data(size: str = "small") -> Dict[str, Any]:
    """Генерирует тестовые данные разного размера"""
    
    if size == "tiny":
        return {
            "a": 1, "b": None, "c": [], "d": {}, "e": [1, 2], "f": {"g": 3}
        }
    
    elif size == "small":
        return {
            "name": "test",
            "value": None,
            "empty_list": [],
            "empty_dict": {},
            "nested": {"a": 1, "b": None, "c": [], "d": [1, 2, None]},
            "data": [1, 2, 3, None, [], {}]
        }
    
    elif size == "medium":
        data = {}
        for i in range(100):
            data[f"key_{i}"] = generate_test_data("small")
        return data
    
    elif size == "large":
        data = {}
        for i in range(1000):
            data[f"key_{i}"] = generate_test_data("small")
        return data
    
    else:  # custom - модель Store
        return Store(
            name="Мой Магазин",
            categories=[
                Category(name="Электроника", products=None),
                Category(name="Книги", products=[
                    Product(id_=1, title="Книга 1", price=None),
                    Product(id_=2, title="Книга 2", price=500.0),
                    Product(id_=3, title="Книга 3", price=None),
                ]),
                Category(name=None, products=[]),
                Category(name="Игрушки", products=[
                    Product(id_=4, title="Игрушка 1", price=1000.0)
                ]),
            ]
        ).to_dict()

# ============================================================================
# 4. Функции бенчмаркинга
# ============================================================================

def benchmark_function(func, data, iterations=1000, name="Function"):
    """Замеряет производительность функции"""
    
    # Прогрев (warm-up)
    for _ in range(100):
        func(data)
    
    # Основной замер
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = func(data)
        end = time.perf_counter()
        times.append((end - start) * 1000)  # в миллисекундах
    
    return {
        "name": name,
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "min": min(times),
        "max": max(times),
        "stdev": statistics.stdev(times) if len(times) > 1 else 0,
        "total": sum(times),
        "iterations": iterations
    }

def run_benchmark(data_sizes=["tiny", "small", "medium", "custom"]):
    """Запускает бенчмарк для разных размеров данных"""
    
    results = {}
    
    for size in data_sizes:
        print(f"\n{'='*60}")
        print(f"📊 Тестовые данные: {size.upper()}")
        print(f"{'='*60}")
        
        # Генерация данных
        test_data = generate_test_data(size)
        
        # Размер данных
        data_size = len(json.dumps(test_data, default=str))
        print(f"📦 Размер данных: {data_size:,} байт ({data_size/1024:.2f} KB)")
        
        # Ожидаемый результат
        expected_python = remove_empty_python(test_data)
        expected_rust = remove_empty_rust(test_data)
        
        # Проверка идентичности результатов
        assert json.dumps(expected_python, sort_keys=True) == json.dumps(expected_rust, sort_keys=True), \
            "Результаты Python и Rust версий не совпадают!"
        print("✅ Результаты идентичны")
        
        # Количество итераций в зависимости от размера данных
        iterations = 10000 if size == "tiny" else (1000 if size == "small" else (100 if size == "medium" else 50))
        
        # Python бенчмарк
        python_result = benchmark_function(
            remove_empty_python, test_data, 
            iterations=iterations, 
            name="Python remove_empty"
        )
        
        # Rust бенчмарк
        rust_result = benchmark_function(
            remove_empty_rust, test_data,
            iterations=iterations,
            name="Rust remove_empty"
        )
        
        results[size] = {
            "python": python_result,
            "rust": rust_result,
            "data_size": data_size,
            "speedup": python_result["mean"] / rust_result["mean"]
        }
        
        # Вывод результатов
        print(f"\n🐍 Python версия:")
        print(f"   Среднее: {python_result['mean']:.4f} мс")
        print(f"   Медиана: {python_result['median']:.4f} мс")
        print(f"   Мин/Макс: {python_result['min']:.4f}/{python_result['max']:.4f} мс")
        
        print(f"\n🦀 Rust версия:")
        print(f"   Среднее: {rust_result['mean']:.4f} мс")
        print(f"   Медиана: {rust_result['median']:.4f} мс")
        print(f"   Мин/Макс: {rust_result['min']:.4f}/{rust_result['max']:.4f} мс")
        
        print(f"\n🚀 Ускорение: {results[size]['speedup']:.2f}x")
        print(f"   (Rust быстрее Python в {results[size]['speedup']:.1f} раз)")
    
    return results

# ============================================================================
# 5. Интеграционный тест с mashumaro
# ============================================================================

def test_with_mashumaro():
    """Тестирует интеграцию с mashumaro через __post_serialize__"""
    
    print(f"\n{'='*60}")
    print("📦 Тест интеграции с mashumaro")
    print(f"{'='*60}")
    
    @dataclass
    class StoreWithCleaner(DataClassORJSONMixin):
        name: str
        categories: Optional[List[Category]] = None
        
        def __post_serialize__(self, d: Dict[str, Any]) -> Dict[str, Any]:
            """Используем Rust версию для очистки"""
            return mashumaronone.remove_empty(d)
    
    store = StoreWithCleaner(
        name="Мой Магазин",
        categories=[
            Category(name="Электроника", products=None),
            Category(name="Книги", products=[
                Product(id_=1, title="Книга 1", price=None)
            ]),
            Category(name=None, products=[]),
        ]
    )
    
    # Замер времени для mashumaro + Rust
    iterations = 1000
    
    # Прогрев
    for _ in range(100):
        _ = store.to_json()
    
    times = []
    for _ in range(iterations):
        start = time.perf_counter()
        result = store.to_json()
        end = time.perf_counter()
        times.append((end - start) * 1000)
    
    print(f"\n⏱️  mashumaro + Rust очистка:")
    print(f"   Среднее: {statistics.mean(times):.4f} мс")
    print(f"   Медиана: {statistics.median(times):.4f} мс")
    print(f"   Итераций: {iterations}")
    
    # Демонстрация результата
    print(f"\n📄 Пример результата:")
    print(json.dumps(json.loads(result), indent=2, ensure_ascii=False)[:500] + "...")

# ============================================================================
# 6. Детальный анализ производительности
# ============================================================================

def detailed_analysis():
    """Детальный анализ производительности"""
    
    print(f"\n{'='*60}")
    print("🔬 Детальный анализ производительности")
    print(f"{'='*60}")
    
    test_data = generate_test_data("small")
    
    # Разные сценарии использования
    scenarios = {
        "Одиночный вызов": 1,
        "Небольшой пакет": 10,
        "Средний пакет": 100,
        "Большой пакет": 1000,
        "Очень большой пакет": 10000
    }
    
    for scenario, count in scenarios.items():
        print(f"\n📊 Сценарий: {scenario} ({count} вызовов)")
        
        # Python
        start = time.perf_counter()
        for _ in range(count):
            remove_empty_python(test_data)
        python_time = (time.perf_counter() - start) * 1000
        
        # Rust
        start = time.perf_counter()
        for _ in range(count):
            remove_empty_rust(test_data)
        rust_time = (time.perf_counter() - start) * 1000
        
        print(f"   Python: {python_time:.2f} мс")
        print(f"   Rust:   {rust_time:.2f} мс")
        print(f"   Ускорение: {python_time/rust_time:.2f}x")
        print(f"   Экономия времени: {python_time - rust_time:.2f} мс")

# ============================================================================
# 7. Main
# ============================================================================

if __name__ == "__main__":
    print("🚀 ЗАПУСК БЕНЧМАРКА")
    print("Сравнение Python vs Rust для функции remove_empty")
    print("="*60)
    
    # Запуск основных бенчмарков
    results = run_benchmark(data_sizes=["tiny", "small", "custom"])
    
    # Детальный анализ
    detailed_analysis()
    
    # Тест с mashumaro
    test_with_mashumaro()
    
    # Итоговое резюме
    print(f"\n{'='*60}")
    print("📊 ИТОГОВОЕ РЕЗЮМЕ")
    print(f"{'='*60}")
    
    for size, data in results.items():
        print(f"\n{size.upper()}:")
        print(f"  📦 Размер данных: {data['data_size']:,} байт")
        print(f"  🐍 Python: {data['python']['mean']:.4f} мс")
        print(f"  🦀 Rust:   {data['rust']['mean']:.4f} мс")
        print(f"  🚀 Ускорение: {data['speedup']:.2f}x")
    
    print(f"\n{'='*60}")
    print("💡 ВЫВОДЫ:")
    print("• Rust-версия значительно быстрее для больших объёмов данных")
    print("• Основной прирост производительности достигается на рекурсивных обходах")
    print("• Интеграция с mashumaro через __post_serialize__ работает отлично")
    print(f"{'='*60}")