#!/usr/bin/env python3
"""
Скрипт для тестирования точности алгоритма выбора модели
Тестирует на папках "Машина" (должны идти в FLASH) и "Рука" (должны идти в PRO)
"""
import os
import asyncio
import time
from pathlib import Path
from typing import List, Tuple, Dict
import cv2
import numpy as np

# Импортируем функцию анализа
from utils.receipt_analyzer import analyze_receipt_and_choose_model


class AccuracyTester:
    def __init__(self):
        self.test_dir = Path("Обучение")
        self.machine_dir = self.test_dir / "Машина"  # Должны идти в FLASH
        self.hand_dir = self.test_dir / "Рука"       # Должны идти в PRO
        
        self.results = {
            'machine': {'correct': 0, 'total': 0, 'details': []},
            'hand': {'correct': 0, 'total': 0, 'details': []}
        }
    
    def load_test_images(self) -> Tuple[List[Tuple[str, str]], List[Tuple[str, str]]]:
        """Загружает пути к тестовым изображениям"""
        machine_images = []
        hand_images = []
        
        # Загружаем изображения "машина" (должны идти в FLASH)
        if self.machine_dir.exists():
            for img_file in self.machine_dir.glob("*.jpg"):
                machine_images.append((str(img_file), "flash"))
        
        # Загружаем изображения "рука" (должны идти в PRO)
        if self.hand_dir.exists():
            for img_file in self.hand_dir.glob("*.jpg"):
                hand_images.append((str(img_file), "pro"))
        
        return machine_images, hand_images
    
    async def test_single_image(self, image_path: str, expected_model: str) -> Dict:
        """Тестирует одно изображение"""
        try:
            print(f"🔍 Тестируем: {os.path.basename(image_path)} (ожидается: {expected_model.upper()})")
            
            # Читаем изображение
            with open(image_path, 'rb') as f:
                image_bytes = f.read()
            
            # Анализируем
            start_time = time.time()
            predicted_model = await analyze_receipt_and_choose_model(image_bytes)
            end_time = time.time()
            
            # Проверяем результат
            is_correct = predicted_model == expected_model
            confidence = "✅" if is_correct else "❌"
            
            result = {
                'image_path': image_path,
                'expected': expected_model,
                'predicted': predicted_model,
                'correct': is_correct,
                'time': end_time - start_time,
                'confidence': confidence
            }
            
            print(f"  {confidence} Предсказано: {predicted_model.upper()}, время: {result['time']:.2f}с")
            
            return result
            
        except Exception as e:
            print(f"  ❌ Ошибка: {e}")
            return {
                'image_path': image_path,
                'expected': expected_model,
                'predicted': 'error',
                'correct': False,
                'time': 0,
                'confidence': "❌",
                'error': str(e)
            }
    
    async def run_tests(self):
        """Запускает все тесты"""
        print("🧪 Запуск тестирования точности алгоритма выбора модели")
        print("=" * 70)
        
        # Загружаем тестовые изображения
        machine_images, hand_images = self.load_test_images()
        
        print(f"📁 Найдено изображений:")
        print(f"  - Машина (должны идти в FLASH): {len(machine_images)}")
        print(f"  - Рука (должны идти в PRO): {len(hand_images)}")
        print()
        
        # Тестируем изображения "машина"
        print("🖨️ Тестируем изображения 'Машина' (печатный текст → FLASH):")
        print("-" * 50)
        
        for image_path, expected in machine_images:
            result = await self.test_single_image(image_path, expected)
            self.results['machine']['details'].append(result)
            self.results['machine']['total'] += 1
            if result['correct']:
                self.results['machine']['correct'] += 1
        
        print()
        
        # Тестируем изображения "рука"
        print("✍️ Тестируем изображения 'Рука' (рукописный текст → PRO):")
        print("-" * 50)
        
        for image_path, expected in hand_images:
            result = await self.test_single_image(image_path, expected)
            self.results['hand']['details'].append(result)
            self.results['hand']['total'] += 1
            if result['correct']:
                self.results['hand']['correct'] += 1
        
        print()
        
        # Выводим результаты
        self.print_results()
    
    def print_results(self):
        """Выводит итоговые результаты"""
        print("📊 РЕЗУЛЬТАТЫ ТЕСТИРОВАНИЯ")
        print("=" * 70)
        
        # Результаты по категориям
        for category, data in self.results.items():
            category_name = "Машина (FLASH)" if category == 'machine' else "Рука (PRO)"
            accuracy = (data['correct'] / data['total'] * 100) if data['total'] > 0 else 0
            
            print(f"\n{category_name}:")
            print(f"  Правильно: {data['correct']}/{data['total']} ({accuracy:.1f}%)")
            
            # Детали по каждому изображению
            for detail in data['details']:
                status = "✅" if detail['correct'] else "❌"
                filename = os.path.basename(detail['image_path'])
                print(f"    {status} {filename}: {detail['predicted'].upper()} (ожидалось: {detail['expected'].upper()})")
        
        # Общие результаты
        total_correct = self.results['machine']['correct'] + self.results['hand']['correct']
        total_images = self.results['machine']['total'] + self.results['hand']['total']
        overall_accuracy = (total_correct / total_images * 100) if total_images > 0 else 0
        
        print(f"\n🎯 ОБЩАЯ ТОЧНОСТЬ: {total_correct}/{total_images} ({overall_accuracy:.1f}%)")
        
        # Проверяем, достигли ли мы цели в 90%
        if overall_accuracy >= 90:
            print("🎉 ЦЕЛЬ ДОСТИГНУТА! Точность >= 90%")
        else:
            print(f"⚠️ Цель не достигнута. Нужно улучшить алгоритм на {90 - overall_accuracy:.1f}%")
        
        # Статистика по времени
        all_times = []
        for category_data in self.results.values():
            for detail in category_data['details']:
                if 'time' in detail and detail['time'] > 0:
                    all_times.append(detail['time'])
        
        if all_times:
            avg_time = sum(all_times) / len(all_times)
            print(f"\n⏱️ Среднее время анализа: {avg_time:.2f} секунд")
    
    def analyze_errors(self):
        """Анализирует ошибки для улучшения алгоритма"""
        print("\n🔍 АНАЛИЗ ОШИБОК")
        print("-" * 30)
        
        errors = []
        for category, data in self.results.items():
            for detail in data['details']:
                if not detail['correct']:
                    errors.append({
                        'category': category,
                        'image': os.path.basename(detail['image_path']),
                        'expected': detail['expected'],
                        'predicted': detail['predicted']
                    })
        
        if not errors:
            print("🎉 Ошибок нет!")
            return
        
        print(f"Найдено {len(errors)} ошибок:")
        for error in errors:
            category_name = "Машина" if error['category'] == 'machine' else "Рука"
            print(f"  - {category_name}: {error['image']} (ожидалось: {error['expected']}, получено: {error['predicted']})")


async def main():
    """Основная функция"""
    tester = AccuracyTester()
    
    try:
        await tester.run_tests()
        tester.analyze_errors()
    except KeyboardInterrupt:
        print("\n⏹️ Тестирование прервано пользователем")
    except Exception as e:
        print(f"\n❌ Ошибка при тестировании: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())