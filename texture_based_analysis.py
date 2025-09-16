#!/usr/bin/env python3
"""
Алгоритм анализа на основе текстуры и структуры изображения
"""

import asyncio
import os
import cv2
import numpy as np
from scipy import ndimage
from skimage import feature, filters, measure
from utils.receipt_analyzer import straighten_receipt

def analyze_texture_features(image: np.ndarray) -> dict:
    """
    Анализирует текстуру изображения для определения типа текста
    """
    try:
        # Преобразуем в оттенки серого
        if len(image.shape) == 3:
            gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        else:
            gray = image
        
        # 1. Анализ локальных бинарных паттернов (LBP)
        lbp = feature.local_binary_pattern(gray, 8, 1, method='uniform')
        lbp_hist, _ = np.histogram(lbp.ravel(), bins=10, range=(0, 10))
        lbp_hist = lbp_hist.astype(float) / lbp_hist.sum()
        lbp_entropy = -np.sum(lbp_hist * np.log2(lbp_hist + 1e-10))
        
        # 2. Анализ градиентов (Sobel)
        sobel_x = filters.sobel_h(gray)
        sobel_y = filters.sobel_v(gray)
        gradient_magnitude = np.sqrt(sobel_x**2 + sobel_y**2)
        
        gradient_mean = np.mean(gradient_magnitude)
        gradient_std = np.std(gradient_magnitude)
        gradient_entropy = -np.sum(gradient_magnitude * np.log2(gradient_magnitude + 1e-10))
        
        # 3. Анализ текстурных характеристик
        # Контраст
        contrast = np.std(gray)
        
        # Энергия (равномерность)
        hist, _ = np.histogram(gray, bins=256, range=(0, 256))
        hist = hist.astype(float) / hist.sum()
        energy = np.sum(hist**2)
        
        # Энтропия
        entropy = -np.sum(hist * np.log2(hist + 1e-10))
        
        # 4. Анализ линий и краев
        edges = cv2.Canny(gray, 50, 150)
        edge_density = np.sum(edges > 0) / edges.size
        
        # Направления градиентов
        gradient_direction = np.arctan2(sobel_y, sobel_x)
        direction_hist, _ = np.histogram(gradient_direction, bins=36, range=(-np.pi, np.pi))
        direction_entropy = -np.sum(direction_hist * np.log2(direction_hist + 1e-10))
        
        # 5. Анализ фрактальной размерности (приближенная)
        # Используем box-counting метод
        def box_counting(image, box_sizes):
            counts = []
            for size in box_sizes:
                # Уменьшаем изображение
                h, w = image.shape
                new_h, new_w = h // size, w // size
                if new_h == 0 or new_w == 0:
                    continue
                
                resized = cv2.resize(image, (new_w, new_h))
                # Считаем количество непустых ячеек
                count = np.sum(resized > 0)
                counts.append(count)
            return counts
        
        binary_image = (gray > 128).astype(np.uint8)
        box_sizes = [1, 2, 4, 8, 16, 32]
        counts = box_counting(binary_image, box_sizes)
        
        if len(counts) > 1:
            # Вычисляем наклон логарифмической зависимости
            log_sizes = np.log(box_sizes[:len(counts)])
            log_counts = np.log(counts)
            if len(log_sizes) > 1:
                fractal_dim = -np.polyfit(log_sizes, log_counts, 1)[0]
            else:
                fractal_dim = 0
        else:
            fractal_dim = 0
        
        # 6. Анализ симметрии
        # Горизонтальная симметрия
        h, w = gray.shape
        top_half = gray[:h//2, :]
        bottom_half = gray[h//2:, :]
        if bottom_half.shape[0] != top_half.shape[0]:
            bottom_half = bottom_half[:top_half.shape[0], :]
        
        horizontal_symmetry = 1.0 - np.mean(np.abs(top_half - np.flipud(bottom_half))) / 255.0
        
        # 7. Анализ регулярности паттернов
        # FFT анализ
        fft = np.fft.fft2(gray)
        fft_shift = np.fft.fftshift(fft)
        magnitude_spectrum = np.log(np.abs(fft_shift) + 1)
        
        # Центральная область спектра
        h, w = magnitude_spectrum.shape
        center_h, center_w = h // 2, w // 2
        center_region = magnitude_spectrum[center_h-20:center_h+20, center_w-20:center_w+20]
        center_energy = np.sum(center_region**2)
        
        # Периферийная область
        mask = np.ones((h, w), dtype=bool)
        mask[center_h-20:center_h+20, center_w-20:center_w+20] = False
        peripheral_region = magnitude_spectrum[mask]
        peripheral_energy = np.sum(peripheral_region**2)
        
        regularity_ratio = center_energy / (peripheral_energy + 1e-10)
        
        return {
            'lbp_entropy': lbp_entropy,
            'gradient_mean': gradient_mean,
            'gradient_std': gradient_std,
            'gradient_entropy': gradient_entropy,
            'contrast': contrast,
            'energy': energy,
            'entropy': entropy,
            'edge_density': edge_density,
            'direction_entropy': direction_entropy,
            'fractal_dimension': fractal_dim,
            'horizontal_symmetry': horizontal_symmetry,
            'regularity_ratio': regularity_ratio
        }
        
    except Exception as e:
        print(f"⚠️ Ошибка при анализе текстуры: {e}")
        return {}

def calculate_texture_chaos_score(features: dict) -> float:
    """
    Вычисляет общий индекс хаоса на основе текстурных характеристик
    """
    if not features:
        return 0.0
    
    try:
        # Нормализуем и объединяем признаки
        chaos_components = []
        
        # 1. Энтропия (высокая энтропия = больше хаоса)
        if 'entropy' in features:
            entropy_norm = min(features['entropy'] / 8.0, 1.0)  # 8 - максимальная энтропия для 8-битного изображения
            chaos_components.append(entropy_norm * 0.15)
        
        # 2. LBP энтропия
        if 'lbp_entropy' in features:
            lbp_norm = min(features['lbp_entropy'] / 3.0, 1.0)  # 3 - примерный максимум для LBP
            chaos_components.append(lbp_norm * 0.15)
        
        # 3. Градиентная энтропия
        if 'gradient_entropy' in features:
            grad_ent_norm = min(features['gradient_entropy'] / 10.0, 1.0)
            chaos_components.append(grad_ent_norm * 0.10)
        
        # 4. Направления градиентов (разнообразие направлений = хаос)
        if 'direction_entropy' in features:
            dir_ent_norm = min(features['direction_entropy'] / 5.0, 1.0)
            chaos_components.append(dir_ent_norm * 0.10)
        
        # 5. Фрактальная размерность (высокая = сложная структура = хаос)
        if 'fractal_dimension' in features:
            fractal_norm = min(features['fractal_dimension'] / 2.0, 1.0)
            chaos_components.append(fractal_norm * 0.10)
        
        # 6. Обратная симметрия (низкая симметрия = хаос)
        if 'horizontal_symmetry' in features:
            asym_norm = 1.0 - features['horizontal_symmetry']
            chaos_components.append(asym_norm * 0.10)
        
        # 7. Обратная регулярность (низкая регулярность = хаос)
        if 'regularity_ratio' in features:
            irregular_norm = 1.0 / (1.0 + features['regularity_ratio'])
            chaos_components.append(irregular_norm * 0.10)
        
        # 8. Плотность краев (высокая плотность = сложная структура)
        if 'edge_density' in features:
            edge_norm = min(features['edge_density'] * 10, 1.0)
            chaos_components.append(edge_norm * 0.10)
        
        # 9. Вариативность градиентов
        if 'gradient_std' in features and 'gradient_mean' in features:
            if features['gradient_mean'] > 0:
                grad_var_norm = min(features['gradient_std'] / features['gradient_mean'], 1.0)
                chaos_components.append(grad_var_norm * 0.10)
        
        # Объединяем все компоненты
        total_chaos = sum(chaos_components) if chaos_components else 0.0
        
        # Применяем нелинейную функцию для усиления различий
        if total_chaos < 0.3:
            total_chaos = total_chaos * 0.5  # Снижаем для низких значений
        elif total_chaos > 0.7:
            total_chaos = 0.7 + (total_chaos - 0.7) * 2.0  # Усиливаем для высоких значений
        
        return min(total_chaos, 1.0)
        
    except Exception as e:
        print(f"⚠️ Ошибка при вычислении индекса хаоса текстуры: {e}")
        return 0.0

async def test_texture_based_analysis():
    """
    Тестирует алгоритм на основе анализа текстуры
    """
    print("🎨 Тестирование алгоритма анализа текстуры")
    print("=" * 60)
    
    # Тестируем печатные чеки
    print("\n📄 Анализ печатных чеков:")
    print("-" * 40)
    
    machine_folder = "обучение/Машина"
    machine_files = [f for f in os.listdir(machine_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    printed_scores = []
    
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
            
            # Выравниваем
            straightened = straighten_receipt(image)
            
            # Анализируем текстуру
            features = analyze_texture_features(straightened)
            chaos_score = calculate_texture_chaos_score(features)
            printed_scores.append(chaos_score)
            
            print(f"  {filename}: {chaos_score:.3f}")
            
        except Exception as e:
            print(f"  {filename}: ошибка - {e}")
    
    # Тестируем рукописные чеки
    print("\n✍️ Анализ рукописных чеков:")
    print("-" * 40)
    
    hand_folder = "обучение/Рука"
    hand_files = [f for f in os.listdir(hand_folder) if f.lower().endswith(('.jpg', '.jpeg', '.png'))]
    
    handwritten_scores = []
    
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
            
            # Выравниваем
            straightened = straighten_receipt(image)
            
            # Анализируем текстуру
            features = analyze_texture_features(straightened)
            chaos_score = calculate_texture_chaos_score(features)
            handwritten_scores.append(chaos_score)
            
            print(f"  {filename}: {chaos_score:.3f}")
            
        except Exception as e:
            print(f"  {filename}: ошибка - {e}")
    
    # Анализ результатов
    if printed_scores and handwritten_scores:
        print(f"\n📊 Сравнение распределений:")
        print(f"Печатные чеки:")
        print(f"  Средний: {np.mean(printed_scores):.3f}")
        print(f"  Медианный: {np.median(printed_scores):.3f}")
        print(f"  Стандартное отклонение: {np.std(printed_scores):.3f}")
        print(f"  Диапазон: {np.min(printed_scores):.3f} - {np.max(printed_scores):.3f}")
        
        print(f"\nРукописные чеки:")
        print(f"  Средний: {np.mean(handwritten_scores):.3f}")
        print(f"  Медианный: {np.median(handwritten_scores):.3f}")
        print(f"  Стандартное отклонение: {np.std(handwritten_scores):.3f}")
        print(f"  Диапазон: {np.min(handwritten_scores):.3f} - {np.max(handwritten_scores):.3f}")
        
        # Поиск оптимального порога
        print(f"\n🎯 Поиск оптимального порога:")
        
        all_scores = printed_scores + handwritten_scores
        all_labels = ['printed'] * len(printed_scores) + ['handwritten'] * len(handwritten_scores)
        
        thresholds = np.arange(0.1, 1.0, 0.05)
        best_threshold = 0.5
        best_accuracy = 0
        
        for threshold in thresholds:
            correct = 0
            total = len(all_scores)
            
            for score, label in zip(all_scores, all_labels):
                predicted = 'pro' if score > threshold else 'flash'
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
    asyncio.run(test_texture_based_analysis())
