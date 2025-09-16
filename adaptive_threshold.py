#!/usr/bin/env python3
"""
Адаптивный алгоритм для определения оптимального порога хаоса
"""

import asyncio
import os
import cv2
import numpy as np
from utils.receipt_analyzer import analyze_receipt_and_choose_model, find_character_contours, group_characters_into_lines, calculate_chaos_index, straighten_receipt

async def analyze_chaos_distribution():
    """
    Анализирует распределение индексов хаоса для определения оптимального порога
    """
    print("📊 Анализ распределения индексов хаоса")
    print("=" * 50)
    
    all_chaos_indices = []
    labels = []
    
    # Анализируем печатные чеки
    machine_folder = "обучение/Машина"
    machine_files = [f for f in os.listdir(machine_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    print(f"\n📄 Анализ печатных чеков ({len(machine_files)} файлов):")
    for filename in machine_files:
        filepath = os.path.join(machine_folder, filename)
        
        try:
            with open(filepath, 'rb') as f:
                image_bytes = f.read()
            
            # Декодируем и обрабатываем изображение
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
            
            file_indices = []
            for line in lines:
                if len(line) >= 2:
                    chaos_index = calculate_chaos_index(line)
                    file_indices.append(chaos_index)
                    all_chaos_indices.append(chaos_index)
                    labels.append('printed')
            
            if file_indices:
                avg_chaos = np.mean(file_indices)
                max_chaos = np.max(file_indices)
                print(f"  {filename}: средний={avg_chaos:.3f}, максимум={max_chaos:.3f}")
            
        except Exception as e:
            print(f"  {filename}: ошибка - {e}")
    
    # Анализируем рукописные чеки
    hand_folder = "обучение/Рука"
    hand_files = [f for f in os.listdir(hand_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    print(f"\n✍️ Анализ рукописных чеков ({len(hand_files)} файлов):")
    for filename in hand_files:
        filepath = os.path.join(hand_folder, filename)
        
        try:
            with open(filepath, 'rb') as f:
                image_bytes = f.read()
            
            # Декодируем и обрабатываем изображение
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
            
            file_indices = []
            for line in lines:
                if len(line) >= 2:
                    chaos_index = calculate_chaos_index(line)
                    file_indices.append(chaos_index)
                    all_chaos_indices.append(chaos_index)
                    labels.append('handwritten')
            
            if file_indices:
                avg_chaos = np.mean(file_indices)
                max_chaos = np.max(file_indices)
                print(f"  {filename}: средний={avg_chaos:.3f}, максимум={max_chaos:.3f}")
            
        except Exception as e:
            print(f"  {filename}: ошибка - {e}")
    
    # Анализ распределения
    if all_chaos_indices:
        printed_indices = [idx for idx, label in zip(all_chaos_indices, labels) if label == 'printed']
        handwritten_indices = [idx for idx, label in zip(all_chaos_indices, labels) if label == 'handwritten']
        
        print(f"\n📈 Статистика распределения:")
        print(f"Всего строк: {len(all_chaos_indices)}")
        print(f"Печатные строки: {len(printed_indices)}")
        print(f"Рукописные строки: {len(handwritten_indices)}")
        
        if printed_indices:
            print(f"\n📄 Печатные чеки:")
            print(f"  Средний индекс хаоса: {np.mean(printed_indices):.3f}")
            print(f"  Медианный индекс хаоса: {np.median(printed_indices):.3f}")
            print(f"  Максимальный индекс хаоса: {np.max(printed_indices):.3f}")
            print(f"  Стандартное отклонение: {np.std(printed_indices):.3f}")
        
        if handwritten_indices:
            print(f"\n✍️ Рукописные чеки:")
            print(f"  Средний индекс хаоса: {np.mean(handwritten_indices):.3f}")
            print(f"  Медианный индекс хаоса: {np.median(handwritten_indices):.3f}")
            print(f"  Максимальный индекс хаоса: {np.max(handwritten_indices):.3f}")
            print(f"  Стандартное отклонение: {np.std(handwritten_indices):.3f}")
        
        # Поиск оптимального порога
        print(f"\n🎯 Поиск оптимального порога:")
        
        # Тестируем разные пороги
        thresholds = np.arange(0.1, 1.0, 0.05)
        best_threshold = 0.5
        best_accuracy = 0
        
        for threshold in thresholds:
            # Симулируем классификацию
            correct = 0
            total = len(all_chaos_indices)
            
            for idx, label in zip(all_chaos_indices, labels):
                predicted = 'pro' if idx > threshold else 'flash'
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
    asyncio.run(analyze_chaos_distribution())
