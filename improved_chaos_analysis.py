#!/usr/bin/env python3
"""
Улучшенный алгоритм анализа хаоса с дополнительными показателями
"""

import asyncio
import os
import cv2
import numpy as np
from utils.receipt_analyzer import find_character_contours, group_characters_into_lines, straighten_receipt

def calculate_improved_chaos_index(line_characters: list) -> float:
    """
    Улучшенный алгоритм вычисления индекса хаоса с дополнительными показателями
    """
    if len(line_characters) < 2:
        return 0.0
    
    try:
        # Базовые характеристики
        heights = [char['h'] for char in line_characters]
        angles = [char['angle'] for char in line_characters]
        center_ys = [char['center_y'] for char in line_characters]
        widths = [char['w'] for char in line_characters]
        
        # 1. Анализ размеров символов
        height_std = np.std(heights) if len(heights) > 1 else 0
        width_std = np.std(widths) if len(widths) > 1 else 0
        avg_height = np.mean(heights)
        avg_width = np.mean(widths)
        
        # Нормализованные показатели размеров
        height_chaos = height_std / avg_height if avg_height > 0 else 0
        width_chaos = width_std / avg_width if avg_width > 0 else 0
        
        # 2. Анализ углов (более строгий)
        # Нормализуем углы к диапазону [-90, 90]
        normalized_angles = []
        for angle in angles:
            while angle > 90:
                angle -= 180
            while angle < -90:
                angle += 180
            normalized_angles.append(abs(angle))  # Берем абсолютное значение
        
        angle_std = np.std(normalized_angles) if len(normalized_angles) > 1 else 0
        angle_chaos = min(angle_std / 10.0, 1.0)  # 10 градусов - максимальный разброс для печатного текста
        
        # 3. Анализ Y-координат (выравнивание строки)
        center_y_std = np.std(center_ys) if len(center_ys) > 1 else 0
        center_y_chaos = center_y_std / avg_height if avg_height > 0 else 0
        
        # 4. Анализ расстояний между символами
        if len(line_characters) > 1:
            distances = []
            for i in range(len(line_characters) - 1):
                char1 = line_characters[i]
                char2 = line_characters[i + 1]
                distance = abs(char2['x'] - (char1['x'] + char1['w']))
                distances.append(distance)
            
            distance_std = np.std(distances) if len(distances) > 1 else 0
            avg_distance = np.mean(distances) if distances else 0
            distance_chaos = distance_std / avg_distance if avg_distance > 0 else 0
        else:
            distance_chaos = 0
        
        # 5. Анализ соотношения сторон символов
        aspect_ratios = [char['w'] / char['h'] for char in line_characters if char['h'] > 0]
        aspect_std = np.std(aspect_ratios) if len(aspect_ratios) > 1 else 0
        avg_aspect = np.mean(aspect_ratios) if aspect_ratios else 1
        aspect_chaos = aspect_std / avg_aspect if avg_aspect > 0 else 0
        
        # 6. Анализ "неровности" строки (вариация Y-координат)
        y_variation = np.var(center_ys) if len(center_ys) > 1 else 0
        y_roughness = min(y_variation / (avg_height ** 2), 1.0) if avg_height > 0 else 0
        
        # 7. Анализ углового разброса (насколько символы "пляшут")
        angle_variance = np.var(normalized_angles) if len(normalized_angles) > 1 else 0
        angle_roughness = min(angle_variance / 100.0, 1.0)  # 100 - максимальная дисперсия
        
        # Объединяем все показатели с весами
        chaos_components = {
            'height': height_chaos * 0.15,
            'width': width_chaos * 0.10,
            'angle': angle_chaos * 0.25,
            'center_y': center_y_chaos * 0.15,
            'distance': distance_chaos * 0.10,
            'aspect': aspect_chaos * 0.10,
            'y_roughness': y_roughness * 0.10,
            'angle_roughness': angle_roughness * 0.05
        }
        
        total_chaos = sum(chaos_components.values())
        
        # Применяем нелинейную функцию для усиления различий
        if total_chaos < 0.3:
            # Для низких значений делаем более консервативную оценку
            total_chaos = total_chaos * 0.7
        elif total_chaos > 0.6:
            # Для высоких значений усиливаем
            total_chaos = 0.6 + (total_chaos - 0.6) * 1.5
        
        return min(total_chaos, 1.0)
        
    except Exception as e:
        print(f"⚠️ Ошибка при вычислении улучшенного индекса хаоса: {e}")
        return 0.0

async def test_improved_algorithm():
    """
    Тестирует улучшенный алгоритм
    """
    print("🚀 Тестирование улучшенного алгоритма анализа хаоса")
    print("=" * 60)
    
    # Тестируем печатные чеки
    print("\n📄 Анализ печатных чеков:")
    print("-" * 40)
    
    machine_folder = "обучение/Машина"
    machine_files = [f for f in os.listdir(machine_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    printed_chaos_values = []
    
    for filename in machine_files:
        filepath = os.path.join(machine_folder, filename)
        
        try:
            with open(filepath, 'rb') as f:
                image_bytes = f.read()
            
            # Обрабатываем изображение
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                continue
            
            # Изменяем размер
            height, width = image.shape[:2]
            max_width = 1000
            if width > max_width:
                scale = max_width / width
                new_width = max_width
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Выравниваем и находим символы
            straightened = straighten_receipt(image)
            gray = cv2.cvtColor(straightened, cv2.COLOR_BGR2GRAY)
            characters = find_character_contours(gray)
            lines = group_characters_into_lines(characters)
            
            file_chaos_values = []
            for line in lines:
                if len(line) >= 2:
                    chaos_index = calculate_improved_chaos_index(line)
                    file_chaos_values.append(chaos_index)
                    printed_chaos_values.append(chaos_index)
            
            if file_chaos_values:
                avg_chaos = np.mean(file_chaos_values)
                max_chaos = np.max(file_chaos_values)
                print(f"  {filename}: средний={avg_chaos:.3f}, максимум={max_chaos:.3f}")
            
        except Exception as e:
            print(f"  {filename}: ошибка - {e}")
    
    # Тестируем рукописные чеки
    print("\n✍️ Анализ рукописных чеков:")
    print("-" * 40)
    
    hand_folder = "обучение/Рука"
    hand_files = [f for f in os.listdir(hand_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    handwritten_chaos_values = []
    
    for filename in hand_files:
        filepath = os.path.join(hand_folder, filename)
        
        try:
            with open(filepath, 'rb') as f:
                image_bytes = f.read()
            
            # Обрабатываем изображение
            nparr = np.frombuffer(image_bytes, np.uint8)
            image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if image is None:
                continue
            
            # Изменяем размер
            height, width = image.shape[:2]
            max_width = 1000
            if width > max_width:
                scale = max_width / width
                new_width = max_width
                new_height = int(height * scale)
                image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
            
            # Выравниваем и находим символы
            straightened = straighten_receipt(image)
            gray = cv2.cvtColor(straightened, cv2.COLOR_BGR2GRAY)
            characters = find_character_contours(gray)
            lines = group_characters_into_lines(characters)
            
            file_chaos_values = []
            for line in lines:
                if len(line) >= 2:
                    chaos_index = calculate_improved_chaos_index(line)
                    file_chaos_values.append(chaos_index)
                    handwritten_chaos_values.append(chaos_index)
            
            if file_chaos_values:
                avg_chaos = np.mean(file_chaos_values)
                max_chaos = np.max(file_chaos_values)
                print(f"  {filename}: средний={avg_chaos:.3f}, максимум={max_chaos:.3f}")
            
        except Exception as e:
            print(f"  {filename}: ошибка - {e}")
    
    # Анализ результатов
    if printed_chaos_values and handwritten_chaos_values:
        print(f"\n📊 Сравнение распределений:")
        print(f"Печатные чеки:")
        print(f"  Средний: {np.mean(printed_chaos_values):.3f}")
        print(f"  Медианный: {np.median(printed_chaos_values):.3f}")
        print(f"  Стандартное отклонение: {np.std(printed_chaos_values):.3f}")
        print(f"  Диапазон: {np.min(printed_chaos_values):.3f} - {np.max(printed_chaos_values):.3f}")
        
        print(f"\nРукописные чеки:")
        print(f"  Средний: {np.mean(handwritten_chaos_values):.3f}")
        print(f"  Медианный: {np.median(handwritten_chaos_values):.3f}")
        print(f"  Стандартное отклонение: {np.std(handwritten_chaos_values):.3f}")
        print(f"  Диапазон: {np.min(handwritten_chaos_values):.3f} - {np.max(handwritten_chaos_values):.3f}")
        
        # Поиск оптимального порога
        print(f"\n🎯 Поиск оптимального порога:")
        
        all_values = printed_chaos_values + handwritten_chaos_values
        all_labels = ['printed'] * len(printed_chaos_values) + ['handwritten'] * len(handwritten_chaos_values)
        
        thresholds = np.arange(0.1, 1.0, 0.05)
        best_threshold = 0.5
        best_accuracy = 0
        
        for threshold in thresholds:
            correct = 0
            total = len(all_values)
            
            for value, label in zip(all_values, all_labels):
                predicted = 'pro' if value > threshold else 'flash'
                expected = 'pro' if label == 'handwritten' else 'flash'
                if predicted == expected:
                    correct += 1
            
            accuracy = correct / total
            print(f"  Порог {threshold:.2f}: точность {accuracy:.3f}")
            
            if accuracy > best_accuracy:
                best_accuracy = accuracy
                best_threshold = threshold
        
        print(f"\n🏆 Оптимальный порог: {best_threshold:.2f} (точность: {best_accuracy:.3f})")
        
        return best_threshold, best_accuracy
    
    return 0.5, 0.0

if __name__ == "__main__":
    asyncio.run(test_improved_algorithm())
