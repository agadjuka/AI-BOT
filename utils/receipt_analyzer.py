"""
Модуль для анализа изображений чеков и обнаружения текстовых регионов.

Содержит функции для предварительной обработки изображений и выделения
областей, которые могут содержать текст.

ВНИМАНИЕ: Этот модуль загружает OpenCV при импорте!
Для оптимизации используйте utils/receipt_analyzer_optimized.py
"""

# Ленивая загрузка OpenCV - загружается только при первом использовании
_cv2 = None

def _get_cv2():
    """Получает OpenCV модуль с ленивой загрузкой"""
    global _cv2
    if _cv2 is None:
        try:
            import cv2
            _cv2 = cv2
            print("🔍 OpenCV загружен для анализа изображения")
        except ImportError as e:
            print(f"❌ Ошибка загрузки OpenCV: {e}")
            raise
    return _cv2

def unload_opencv():
    """Выгружает OpenCV из памяти для освобождения ресурсов"""
    global _cv2
    if _cv2 is not None:
        try:
            print("🧹 Выгружаем OpenCV из памяти...")
            
            # Очищаем кэш OpenCV (если доступно)
            try:
                if hasattr(_cv2, 'destroyAllWindows'):
                    _cv2.destroyAllWindows()
            except Exception:
                # Игнорируем ошибки destroyAllWindows (не критично)
                pass
            
            # Очищаем глобальную переменную
            _cv2 = None
            
            # Принудительная сборка мусора
            import gc
            gc.collect()
            
            print("✅ OpenCV выгружен из памяти")
            
        except Exception as e:
            print(f"⚠️ Ошибка при выгрузке OpenCV: {e}")
            # Не поднимаем исключение - это не критично

import numpy as np
from typing import List, Tuple, Dict
import asyncio
import math
from skimage.feature import local_binary_pattern
from scipy.stats import entropy


async def find_text_regions(image_bytes: bytes) -> List[Tuple[int, int, int, int]]:
    """
    Асинхронная функция для обнаружения текстовых регионов на изображении.
    
    Args:
        image_bytes: Изображение в виде байтов
        
    Returns:
        Список прямоугольников текстовых областей в формате (x, y, w, h)
    """
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Декодирование изображения из байтов
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return []
        
        # Изменение размера для ускорения обработки
        height, width = image.shape[:2]
        max_width = 1000
        
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Преобразование в оттенки серого
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Предварительная обработка для улучшения качества
        # Применяем размытие по Гауссу для уменьшения шума
        blurred = cv2.GaussianBlur(gray, (3, 3), 0)
        
        # Используем MSER для обнаружения текстовых регионов
        mser = cv2.MSER_create(
            min_area=20,      # Минимальная площадь региона
            max_area=10000,   # Максимальная площадь региона
            max_variation=0.25,  # Максимальная вариация
            min_diversity=0.2,   # Минимальное разнообразие
            max_evolution=200,   # Максимальная эволюция
            area_threshold=1.01, # Порог площади
            min_margin=0.003,    # Минимальный отступ
            edge_blur_size=5     # Размер размытия краев
        )
        
        # Обнаружение регионов
        regions, _ = mser.detectRegions(blurred)
        
        if not regions:
            return []
        
        # Фильтрация регионов по геометрическим признакам
        filtered_regions = []
        for region in regions:
            # Получаем ограничивающий прямоугольник
            x, y, w, h = cv2.boundingRect(region)
            
            # Фильтруем по размеру
            if w < 5 or h < 5 or w > 200 or h > 200:
                continue
                
            # Фильтруем по соотношению сторон (исключаем слишком вытянутые)
            aspect_ratio = w / h
            if aspect_ratio < 0.1 or aspect_ratio > 10:
                continue
                
            # Фильтруем по площади
            area = w * h
            if area < 25 or area > 20000:
                continue
                
            filtered_regions.append((x, y, w, h))
        
        if not filtered_regions:
            return []
        
        # Группировка близко расположенных регионов в строки
        text_regions = _group_regions_into_lines(filtered_regions)
        
        return text_regions
        
    except Exception as e:
        print(f"Ошибка при анализе изображения: {e}")
        return []


def _group_regions_into_lines(regions: List[Tuple[int, int, int, int]]) -> List[Tuple[int, int, int, int]]:
    """
    Группирует близко расположенные регионы в строки текста.
    
    Args:
        regions: Список прямоугольников регионов
        
    Returns:
        Список сгруппированных прямоугольников
    """
    if not regions:
        return []
    
    # Сортируем регионы по вертикальной позиции
    regions.sort(key=lambda r: r[1])
    
    lines = []
    current_line = [regions[0]]
    
    for i in range(1, len(regions)):
        current_region = regions[i]
        last_region = current_line[-1]
        
        # Проверяем, можно ли добавить регион к текущей строке
        # Регионы считаются на одной строке, если их вертикальные центры близки
        current_center_y = current_region[1] + current_region[3] // 2
        last_center_y = last_region[1] + last_region[3] // 2
        
        # Максимальное расстояние по вертикали для группировки в строку
        max_vertical_distance = max(current_region[3], last_region[3]) * 0.5
        
        if abs(current_center_y - last_center_y) <= max_vertical_distance:
            current_line.append(current_region)
        else:
            # Завершаем текущую строку и начинаем новую
            lines.append(_merge_regions_in_line(current_line))
            current_line = [current_region]
    
    # Добавляем последнюю строку
    if current_line:
        lines.append(_merge_regions_in_line(current_line))
    
    return lines


def _merge_regions_in_line(regions: List[Tuple[int, int, int, int]]) -> Tuple[int, int, int, int]:
    """
    Объединяет регионы в одной строке в один прямоугольник.
    
    Args:
        regions: Список прямоугольников в одной строке
        
    Returns:
        Объединенный прямоугольник
    """
    if not regions:
        return (0, 0, 0, 0)
    
    if len(regions) == 1:
        return regions[0]
    
    # Находим границы объединенного прямоугольника
    min_x = min(r[0] for r in regions)
    min_y = min(r[1] for r in regions)
    max_x = max(r[0] + r[2] for r in regions)
    max_y = max(r[1] + r[3] for r in regions)
    
    return (min_x, min_y, max_x - min_x, max_y - min_y)


def straighten_receipt(image: np.ndarray) -> np.ndarray:
    """
    Выравнивает изображение чека, исправляя наклон.
    
    Args:
        image: Исходное изображение
        
    Returns:
        Выровненное изображение
    """
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Преобразуем в оттенки серого
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # Применяем размытие для уменьшения шума
        blurred = cv2.GaussianBlur(gray, (5, 5), 0)
        
        # Используем детектор краев Canny
        edges = cv2.Canny(blurred, 50, 150, apertureSize=3)
        
        # Находим линии с помощью преобразования Хафа
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=100)
        
        if lines is None or len(lines) == 0:
            return image
        
        # Вычисляем средний угол наклона
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = theta * 180 / np.pi
            # Нормализуем угол к диапазону [-45, 45]
            if angle > 45:
                angle -= 90
            elif angle < -45:
                angle += 90
            angles.append(angle)
        
        if not angles:
            return image
        
        # Вычисляем медианный угол для устойчивости к выбросам
        median_angle = np.median(angles)
        
        # Если угол небольшой, не поворачиваем
        if abs(median_angle) < 1:
            return image
        
        # Поворачиваем изображение
        height, width = image.shape[:2]
        center = (width // 2, height // 2)
        rotation_matrix = cv2.getRotationMatrix2D(center, median_angle, 1.0)
        
        # Вычисляем новые размеры изображения
        cos_angle = abs(rotation_matrix[0, 0])
        sin_angle = abs(rotation_matrix[0, 1])
        new_width = int((height * sin_angle) + (width * cos_angle))
        new_height = int((height * cos_angle) + (width * sin_angle))
        
        # Корректируем матрицу поворота для центрирования
        rotation_matrix[0, 2] += (new_width / 2) - center[0]
        rotation_matrix[1, 2] += (new_height / 2) - center[1]
        
        # Применяем поворот
        straightened = cv2.warpAffine(image, rotation_matrix, (new_width, new_height), 
                                    flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)
        
        return straightened
        
    except Exception as e:
        print(f"⚠️ Ошибка при выравнивании изображения: {e}")
        return image


def find_character_contours(image: np.ndarray) -> List[Dict]:
    """
    Находит контуры всех отдельных символов на изображении.
    
    Args:
        image: Выровненное изображение в оттенках серого
        
    Returns:
        Список словарей с информацией о символах: {'contour', 'x', 'y', 'w', 'h', 'angle'}
    """
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Применяем адаптивную бинаризацию
        binary = cv2.adaptiveThreshold(
            image, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2
        )
        
        # Более агрессивные морфологические операции для очистки
        kernel_small = cv2.getStructuringElement(cv2.MORPH_RECT, (2, 2))
        kernel_medium = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        # Удаляем мелкий шум
        binary = cv2.morphologyEx(binary, cv2.MORPH_OPEN, kernel_small)
        # Закрываем разрывы в символах
        binary = cv2.morphologyEx(binary, cv2.MORPH_CLOSE, kernel_medium)
        
        # Находим контуры
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        characters = []
        for contour in contours:
            # Получаем ограничивающий прямоугольник
            x, y, w, h = cv2.boundingRect(contour)
            
            # Более строгие фильтры по размеру
            if w < 8 or h < 8 or w > 80 or h > 80:
                continue
            
            # Фильтруем по соотношению сторон (исключаем слишком вытянутые)
            aspect_ratio = w / h
            if aspect_ratio < 0.2 or aspect_ratio > 5:
                continue
            
            # Фильтруем по площади
            area = cv2.contourArea(contour)
            if area < 50 or area > 2000:
                continue
            
            # Фильтруем по компактности (отношение площади контура к площади прямоугольника)
            rect_area = w * h
            compactness = area / rect_area if rect_area > 0 else 0
            if compactness < 0.3:  # Исключаем слишком "дырявые" объекты
                continue
            
            # Вычисляем угол наклона символа
            if len(contour) >= 5:
                try:
                    ellipse = cv2.fitEllipse(contour)
                    angle = ellipse[2]
                    # Нормализуем угол к диапазону [-90, 90]
                    if angle > 90:
                        angle -= 180
                    elif angle < -90:
                        angle += 180
                except:
                    angle = 0
            else:
                angle = 0
            
            characters.append({
                'contour': contour,
                'x': x,
                'y': y,
                'w': w,
                'h': h,
                'angle': angle,
                'center_y': y + h // 2
            })
        
        return characters
        
    except Exception as e:
        print(f"⚠️ Ошибка при поиске контуров символов: {e}")
        return []


def group_characters_into_lines(characters: List[Dict]) -> List[List[Dict]]:
    """
    Группирует символы в строки на основе их Y-координаты.
    
    Args:
        characters: Список символов с их характеристиками
        
    Returns:
        Список строк, где каждая строка - это список символов
    """
    if not characters:
        return []
    
    # Сортируем символы по Y-координате
    characters.sort(key=lambda c: c['center_y'])
    
    lines = []
    current_line = [characters[0]]
    
    for i in range(1, len(characters)):
        current_char = characters[i]
        last_char = current_line[-1]
        
        # Вычисляем расстояние по вертикали между символами
        vertical_distance = abs(current_char['center_y'] - last_char['center_y'])
        
        # Вычисляем среднюю высоту символов в текущей строке
        avg_height = np.mean([char['h'] for char in current_line])
        
        # Максимальное расстояние для группировки в строку (50% от средней высоты)
        max_distance = avg_height * 0.5
        
        if vertical_distance <= max_distance:
            current_line.append(current_char)
        else:
            # Завершаем текущую строку и начинаем новую
            lines.append(current_line)
            current_line = [current_char]
    
    # Добавляем последнюю строку
    if current_line:
        lines.append(current_line)
    
    return lines


def calculate_chaos_index(line_characters: List[Dict]) -> float:
    """
    Вычисляет индекс хаоса для строки символов.
    
    Args:
        line_characters: Список символов в строке
        
    Returns:
        Индекс хаоса (0-1, где 1 - максимальный хаос)
    """
    if len(line_characters) < 2:
        return 0.0
    
    try:
        # Собираем характеристики символов
        heights = [char['h'] for char in line_characters]
        angles = [char['angle'] for char in line_characters]
        center_ys = [char['center_y'] for char in line_characters]
        
        # Вычисляем стандартные отклонения
        height_std = np.std(heights) if len(heights) > 1 else 0
        angle_std = np.std(angles) if len(angles) > 1 else 0
        center_y_std = np.std(center_ys) if len(center_ys) > 1 else 0
        
        # Нормализуем стандартные отклонения
        avg_height = np.mean(heights)
        height_chaos = height_std / avg_height if avg_height > 0 else 0
        
        # Углы нормализуем более консервативно
        # Для печатного текста углы должны быть близки к 0
        angle_chaos = min(angle_std / 15.0, 1.0)  # 15 градусов - максимальный разброс для печатного текста
        
        # Y-координаты нормализуем относительно средней высоты
        center_y_chaos = center_y_std / avg_height if avg_height > 0 else 0
        
        # Дополнительная проверка: если все углы близки к 0, это печатный текст
        angle_variance = np.var(angles)
        if angle_variance < 25:  # Если дисперсия углов мала
            angle_chaos *= 0.5  # Снижаем вклад углов
        
        # Объединяем показатели с весами
        chaos_index = (height_chaos * 0.3 + angle_chaos * 0.4 + center_y_chaos * 0.3)
        
        # Применяем нелинейную функцию для более четкого разделения
        if chaos_index < 0.2:
            chaos_index *= 0.5  # Снижаем для низких значений
        elif chaos_index > 0.6:
            chaos_index = 0.5 + (chaos_index - 0.6) * 1.25  # Усиливаем для высоких значений
        
        return min(chaos_index, 1.0)  # Ограничиваем максимумом 1.0
        
    except Exception as e:
        print(f"⚠️ Ошибка при вычислении индекса хаоса: {e}")
        return 0.0


def find_table_region(text_regions: List[Tuple[int, int, int, int]], image_height: int, image_width: int) -> List[Tuple[int, int, int, int]]:
    """
    Находит область таблицы товаров, исключая заголовки и подписи.
    
    Args:
        text_regions: Список всех найденных текстовых блоков
        image_height: Высота изображения
        image_width: Ширина изображения
        
    Returns:
        Список блоков, принадлежащих таблице товаров
    """
    if not text_regions:
        return []
    
    # Сортируем блоки по Y-координате
    sorted_regions = sorted(text_regions, key=lambda r: r[1])
    
    # Исключаем верхние 20% изображения (заголовки, адреса) - менее агрессивно
    header_threshold = int(image_height * 0.2)
    
    # Исключаем нижние 15% изображения (подписи, итоги) - менее агрессивно
    footer_threshold = int(image_height * 0.85)
    
    # Исключаем боковые области (могут содержать логотипы, номера) - менее агрессивно
    side_margin = int(image_width * 0.05)
    
    table_regions = []
    for x, y, w, h in sorted_regions:
        # Проверяем, что блок находится в центральной области
        if (y > header_threshold and 
            y + h < footer_threshold and
            x > side_margin and 
            x + w < image_width - side_margin):
            
            # Дополнительная фильтрация по размеру блока
            # Исключаем слишком маленькие и слишком большие блоки
            if (w > 20 and h > 10 and w < image_width * 0.8 and h < image_height * 0.3):
                table_regions.append((x, y, w, h))
    
    print(f"🔍 Найдено {len(table_regions)} блоков в области таблицы из {len(text_regions)} общих")
    return table_regions


async def analyze_receipt_and_choose_model(image_bytes: bytes) -> str:
    """
    Анализирует изображение чека и выбирает подходящую модель для обработки.
    Использует анализ текстуры блоков с помощью LBP (Local Binary Pattern).
    
    Args:
        image_bytes: Изображение в виде байтов
        
    Returns:
        'flash' для печатного текста или 'pro' для рукописного текста
    """
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Шаг 1: Подготовка - декодируем изображение
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            print("❌ Ошибка декодирования изображения, используем модель flash")
            return 'flash'
        
        # Изменяем размер для ускорения обработки
        height, width = image.shape[:2]
        max_width = 1000
        
        if width > max_width:
            scale = max_width / width
            new_width = max_width
            new_height = int(height * scale)
            image = cv2.resize(image, (new_width, new_height), interpolation=cv2.INTER_AREA)
        
        # Шаг 2: Выравнивание изображения
        print("🔍 Выравниваем изображение...")
        straightened_image = straighten_receipt(image)
        
        # Преобразуем в оттенки серого
        gray = cv2.cvtColor(straightened_image, cv2.COLOR_BGR2GRAY)
        
        # Шаг 3: Находим все текстовые блоки на изображении
        print("🔍 Ищем текстовые блоки...")
        text_regions = await find_text_regions(image_bytes)
        
        if not text_regions:
            print("🔍 Текстовые блоки не найдены, используем модель flash")
            return 'flash'
        
        print(f"🔍 Найдено {len(text_regions)} текстовых блоков")
        
        # Шаг 4: Фильтруем только блоки таблицы товаров
        print("🔍 Фильтруем блоки таблицы товаров...")
        table_regions = find_table_region(text_regions, gray.shape[0], gray.shape[1])
        
        if not table_regions:
            print("🔍 Блоки таблицы не найдены, используем модель flash")
            return 'flash'
        
        # Шаг 5: Улучшенный анализ с множественными метриками
        # Анализируем общие характеристики всех блоков таблицы
        
        total_blocks = len(table_regions)
        if total_blocks == 0:
            print("🔍 Блоки таблицы не найдены, используем модель flash")
            return 'flash'
        
        # Собираем метрики для всех блоков
        block_metrics = []
        large_blocks = 0
        high_density_blocks = 0
        irregular_blocks = 0
        high_contrast_blocks = 0
        size_variance_blocks = 0
        
        # Собираем размеры блоков для анализа вариативности
        block_areas = []
        
        for x, y, w, h in table_regions:
            area = w * h
            block_areas.append(area)
            
            # Блок считается большим, если его площадь больше 2000 пикселей
            if area > 2000:
                large_blocks += 1
            
            # Анализируем плотность блока
            block_roi = gray[y:y+h, x:x+w]
            binary = cv2.adaptiveThreshold(block_roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            black_pixels = np.sum(binary > 0)
            total_pixels = binary.size
            density = black_pixels / total_pixels if total_pixels > 0 else 0
            
            # Блок считается плотным, если плотность > 0.3
            if density > 0.3:
                high_density_blocks += 1
            
            # Анализируем неровность краев
            edges = cv2.Canny(block_roi, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size if edges.size > 0 else 0
            
            # Блок считается неровным, если плотность краев > 0.1
            if edge_density > 0.1:
                irregular_blocks += 1
            
            # Анализируем контраст блока
            mean_intensity = np.mean(block_roi)
            std_intensity = np.std(block_roi)
            contrast = std_intensity / (mean_intensity + 1e-6)  # Избегаем деления на ноль
            
            # Блок считается высококонтрастным, если контраст > 0.3
            if contrast > 0.3:
                high_contrast_blocks += 1
            
            # Сохраняем метрики блока
            block_metrics.append({
                'area': area,
                'density': density,
                'edge_density': edge_density,
                'contrast': contrast,
                'w': w,
                'h': h
            })
        
        # Анализируем вариативность размеров блоков
        if len(block_areas) > 1:
            area_std = np.std(block_areas)
            area_mean = np.mean(block_areas)
            area_cv = area_std / (area_mean + 1e-6)  # Коэффициент вариации
            
            # Если вариативность размеров высокая (> 0.5), это может указывать на рукописный текст
            if area_cv > 0.5:
                size_variance_blocks = total_blocks
        else:
            area_cv = 0
        
        # Вычисляем процентные соотношения
        large_blocks_ratio = large_blocks / total_blocks
        high_density_ratio = high_density_blocks / total_blocks
        irregular_ratio = irregular_blocks / total_blocks
        high_contrast_ratio = high_contrast_blocks / total_blocks
        size_variance_ratio = size_variance_blocks / total_blocks
        
        # Финальный подход: комбинированный анализ с мягкими порогами
        # Анализируем множественные признаки с разными весами
        
        # Собираем метрики для всех блоков
        density_scores = []
        contrast_scores = []
        irregular_scores = []
        
        for x, y, w, h in table_regions:
            block_roi = gray[y:y+h, x:x+w]
            
            # Анализируем плотность блока
            binary = cv2.adaptiveThreshold(block_roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
            black_pixels = np.sum(binary > 0)
            total_pixels = binary.size
            density = black_pixels / total_pixels if total_pixels > 0 else 0
            density_scores.append(density)
            
            # Анализируем контраст блока
            mean_intensity = np.mean(block_roi)
            std_intensity = np.std(block_roi)
            contrast = std_intensity / (mean_intensity + 1e-6)
            contrast_scores.append(contrast)
            
            # Анализируем неровность краев
            edges = cv2.Canny(block_roi, 50, 150)
            edge_density = np.sum(edges > 0) / edges.size if edges.size > 0 else 0
            irregular_scores.append(edge_density)
        
        # Вычисляем средние значения
        avg_density = np.mean(density_scores)
        avg_contrast = np.mean(contrast_scores)
        avg_irregular = np.mean(irregular_scores)
        
        # Подсчитываем блоки с высокими значениями (мягкие пороги)
        high_density_count = sum(1 for d in density_scores if d > 0.25)
        high_contrast_count = sum(1 for c in contrast_scores if c > 0.3)
        high_irregular_count = sum(1 for i in irregular_scores if i > 0.05)
        
        # Вычисляем процентные соотношения
        density_ratio = high_density_count / total_blocks
        contrast_ratio = high_contrast_count / total_blocks
        irregular_ratio = high_irregular_count / total_blocks
        
        # Комбинированный score с весами
        handwritten_score = (
            density_ratio * 0.4 +      # Плотность - главный индикатор
            contrast_ratio * 0.3 +     # Контраст
            irregular_ratio * 0.3      # Неровность
        )
        
        print(f"🔍 Анализ таблицы: {total_blocks} блоков")
        print(f"   Плотных (>0.25): {density_ratio:.2f}, Высококонтрастных (>0.3): {contrast_ratio:.2f}")
        print(f"   Неровных (>0.05): {irregular_ratio:.2f}")
        print(f"   Итоговый score: {handwritten_score:.2f}")
        
        # Оптимальный порог для баланса между точностью и чувствительностью
        HANDWRITTEN_THRESHOLD = 0.35
        
        # Принимаем решение на основе улучшенного анализа
        if handwritten_score > HANDWRITTEN_THRESHOLD:
            print("✍️ Выбрана модель PRO (рукописный текст)")
            return 'pro'
        else:
            print("🖨️ Выбрана модель FLASH (печатный текст)")
            return 'flash'
            
    except Exception as e:
        print(f"❌ Ошибка при анализе чека: {e}")
        # В случае ошибки используем более мощную модель
        return 'pro'


def _analyze_text_density(binary_roi: np.ndarray) -> float:
    """
    Анализирует плотность текста в бинаризованном ROI.
    
    Args:
        binary_roi: Бинаризованное изображение ROI
        
    Returns:
        Плотность текста (отношение черных пикселей к общему количеству)
    """
    total_pixels = binary_roi.size
    black_pixels = np.sum(binary_roi == 0)  # Черные пиксели (текст)
    
    return black_pixels / total_pixels if total_pixels > 0 else 0


def _analyze_line_variation(binary_roi: np.ndarray) -> float:
    """
    Анализирует вариативность толщины линий в ROI.
    
    Args:
        binary_roi: Бинаризованное изображение ROI
        
    Returns:
        Коэффициент вариации толщины линий
    """
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Применяем морфологические операции для анализа толщины линий
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        
        # Эрозия для получения тонких линий
        eroded = cv2.erode(binary_roi, kernel, iterations=1)
        
        # Дилатация для восстановления
        dilated = cv2.dilate(eroded, kernel, iterations=1)
        
        # Разность показывает вариативность толщины
        difference = cv2.absdiff(binary_roi, dilated)
        
        # Вычисляем коэффициент вариации
        diff_pixels = np.sum(difference > 0)
        total_pixels = binary_roi.size
        
        return diff_pixels / total_pixels if total_pixels > 0 else 0
        
    except Exception as e:
        print(f"⚠️ Ошибка анализа вариации линий: {e}")
        return 0


def _is_handwritten_block(text_density: float, line_variation: float) -> bool:
    """
    Определяет, является ли текстовый блок рукописным.
    
    Args:
        text_density: Плотность текста
        line_variation: Вариативность толщины линий
        
    Returns:
        True если блок считается рукописным
    """
    # Пороговые значения для определения рукописного текста
    density_threshold = 0.35  # Высокая плотность текста
    variation_threshold = 0.15  # Высокая вариативность толщины
    
    # Блок считается рукописным, если:
    # 1. Высокая плотность текста ИЛИ
    # 2. Высокая вариативность толщины линий
    return (text_density > density_threshold or 
            line_variation > variation_threshold)


# Дополнительная функция для отладки и визуализации
def _analyze_size_variance(block_roi: np.ndarray) -> float:
    """Анализирует вариацию размеров символов в блоке"""
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Применяем морфологические операции для выделения символов
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        binary = cv2.adaptiveThreshold(block_roi, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 11, 2)
        
        # Находим контуры
        contours, _ = cv2.findContours(binary, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        if len(contours) < 2:
            return 0.0
        
        # Вычисляем площади контуров
        areas = [cv2.contourArea(contour) for contour in contours if cv2.contourArea(contour) > 10]
        
        if len(areas) < 2:
            return 0.0
        
        # Вычисляем коэффициент вариации
        mean_area = np.mean(areas)
        std_area = np.std(areas)
        cv = std_area / mean_area if mean_area > 0 else 0
        
        return min(cv, 1.0)  # Нормализуем к [0, 1]
    except:
        return 0.0


def _analyze_angle_variance(block_roi: np.ndarray) -> float:
    """Анализирует вариацию углов наклона в блоке"""
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Применяем детектор краев
        edges = cv2.Canny(block_roi, 50, 150)
        
        # Находим линии
        lines = cv2.HoughLines(edges, 1, np.pi/180, threshold=30)
        
        if lines is None or len(lines) < 2:
            return 0.0
        
        # Вычисляем углы
        angles = []
        for line in lines:
            rho, theta = line[0]
            angle = theta * 180 / np.pi
            # Нормализуем угол к диапазону [-90, 90]
            if angle > 90:
                angle -= 180
            elif angle < -90:
                angle += 180
            angles.append(angle)
        
        # Вычисляем стандартное отклонение углов
        angle_std = np.std(angles)
        normalized_std = min(angle_std / 45.0, 1.0)  # Нормализуем к [0, 1]
        
        return normalized_std
    except:
        return 0.0


def _analyze_density_variance(block_roi: np.ndarray) -> float:
    """Анализирует вариацию плотности текста в блоке"""
    try:
        # Разделяем блок на небольшие области
        h, w = block_roi.shape
        region_h, region_w = h // 4, w // 4
        
        if region_h < 2 or region_w < 2:
            return 0.0
        
        densities = []
        for i in range(0, h - region_h, region_h):
            for j in range(0, w - region_w, region_w):
                region = block_roi[i:i+region_h, j:j+region_w]
                # Вычисляем плотность черных пикселей
                density = np.sum(region < 128) / region.size
                densities.append(density)
        
        if len(densities) < 2:
            return 0.0
        
        # Вычисляем коэффициент вариации плотности
        mean_density = np.mean(densities)
        std_density = np.std(densities)
        cv = std_density / mean_density if mean_density > 0 else 0
        
        return min(cv, 1.0)  # Нормализуем к [0, 1]
    except:
        return 0.0


def _analyze_contrast_variance(block_roi: np.ndarray) -> float:
    """Анализирует вариацию контраста в блоке"""
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Вычисляем локальный контраст
        kernel = np.array([[-1, -1, -1], [-1, 8, -1], [-1, -1, -1]])
        contrast = cv2.filter2D(block_roi.astype(np.float32), -1, kernel)
        
        # Вычисляем вариацию контраста
        contrast_std = np.std(contrast)
        normalized_std = min(contrast_std / 100.0, 1.0)  # Нормализуем к [0, 1]
        
        return normalized_std
    except:
        return 0.0


def visualize_text_regions(image_bytes: bytes, regions: List[Tuple[int, int, int, int]]) -> bytes:
    """
    Создает визуализацию найденных текстовых регионов.
    
    Args:
        image_bytes: Исходное изображение в байтах
        regions: Список прямоугольников текстовых областей
        
    Returns:
        Изображение с отмеченными регионами в байтах
    """
    try:
        # Получаем OpenCV с ленивой загрузкой
        cv2 = _get_cv2()
        
        # Декодируем изображение
        nparr = np.frombuffer(image_bytes, np.uint8)
        image = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
        
        if image is None:
            return b''
        
        # Рисуем прямоугольники вокруг найденных регионов
        for x, y, w, h in regions:
            cv2.rectangle(image, (x, y), (x + w, y + h), (0, 255, 0), 2)
        
        # Кодируем обратно в байты
        _, encoded_img = cv2.imencode('.jpg', image)
        return encoded_img.tobytes()
        
    except Exception as e:
        print(f"Ошибка при создании визуализации: {e}")
        return b''
