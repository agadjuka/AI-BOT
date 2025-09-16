"""
Оптимизированный модуль для анализа изображений чеков с ленивой загрузкой OpenCV
OpenCV загружается только при необходимости и выгружается после использования
"""
import numpy as np
from typing import List, Tuple, Dict
import asyncio
import math
from skimage.feature import local_binary_pattern
from scipy.stats import entropy

# Импортируем ленивый загрузчик OpenCV
from utils.opencv_lazy_loader import with_opencv_async, OpenCVContext, check_opencv_availability


async def find_text_regions(image_bytes: bytes) -> List[Tuple[int, int, int, int]]:
    """
    Асинхронная функция для обнаружения текстовых регионов на изображении.
    OpenCV загружается только при вызове этой функции.
    
    Args:
        image_bytes: Изображение в виде байтов
        
    Returns:
        Список прямоугольников текстовых областей в формате (x, y, w, h)
    """
    # Проверяем доступность OpenCV
    if not check_opencv_availability():
        print("❌ OpenCV недоступен, возвращаем пустой список")
        return []
    
    try:
        # Используем контекстный менеджер для автоматической загрузки/выгрузки OpenCV
        with OpenCVContext() as cv2:
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
            blurred = cv2.GaussianBlur(gray, (3, 3), 0)
            
            # Используем MSER для обнаружения текстовых регионов
            mser = cv2.MSER_create(
                min_area=20,
                max_area=10000,
                max_variation=0.25,
                min_diversity=0.2,
                max_evolution=200,
                area_threshold=1.01,
                min_margin=0.003,
                edge_blur_size=5
            )
            
            # Обнаружение регионов
            regions, _ = mser.detectRegions(blurred)
            
            if not regions:
                return []
            
            # Фильтрация регионов по геометрическим признакам
            filtered_regions = []
            for region in regions:
                x, y, w, h = cv2.boundingRect(region)
                
                # Фильтруем по размеру
                if w < 5 or h < 5 or w > 200 or h > 200:
                    continue
                    
                # Фильтруем по соотношению сторон
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


async def straighten_receipt(image: np.ndarray) -> np.ndarray:
    """
    Выравнивает изображение чека, исправляя наклон.
    OpenCV загружается только при вызове этой функции.
    """
    if not check_opencv_availability():
        print("❌ OpenCV недоступен, возвращаем исходное изображение")
        return image
    
    try:
        with OpenCVContext() as cv2:
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


async def analyze_receipt_and_choose_model(image_bytes: bytes) -> str:
    """
    Анализирует изображение чека и выбирает подходящую модель для обработки.
    OpenCV загружается только при вызове этой функции и выгружается после.
    
    Args:
        image_bytes: Изображение в виде байтов
        
    Returns:
        'flash' для печатного текста или 'pro' для рукописного текста
    """
    if not check_opencv_availability():
        print("❌ OpenCV недоступен, используем модель flash")
        return 'flash'
    
    try:
        with OpenCVContext() as cv2:
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
            straightened_image = await straighten_receipt(image)
            
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
            
            # Шаг 5: Анализ характеристик блоков
            total_blocks = len(table_regions)
            if total_blocks == 0:
                print("🔍 Блоки таблицы не найдены, используем модель flash")
                return 'flash'
            
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
            
            # Подсчитываем блоки с высокими значениями
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


def find_table_region(text_regions: List[Tuple[int, int, int, int]], image_height: int, image_width: int) -> List[Tuple[int, int, int, int]]:
    """
    Находит область таблицы товаров, исключая заголовки и подписи.
    """
    if not text_regions:
        return []
    
    # Сортируем блоки по Y-координате
    sorted_regions = sorted(text_regions, key=lambda r: r[1])
    
    # Исключаем верхние 20% изображения (заголовки, адреса)
    header_threshold = int(image_height * 0.2)
    
    # Исключаем нижние 15% изображения (подписи, итоги)
    footer_threshold = int(image_height * 0.85)
    
    # Исключаем боковые области (могут содержать логотипы, номера)
    side_margin = int(image_width * 0.05)
    
    table_regions = []
    for x, y, w, h in sorted_regions:
        # Проверяем, что блок находится в центральной области
        if (y > header_threshold and 
            y + h < footer_threshold and
            x > side_margin and 
            x + w < image_width - side_margin):
            
            # Дополнительная фильтрация по размеру блока
            if (w > 20 and h > 10 and w < image_width * 0.8 and h < image_height * 0.3):
                table_regions.append((x, y, w, h))
    
    print(f"🔍 Найдено {len(table_regions)} блоков в области таблицы из {len(text_regions)} общих")
    return table_regions


async def visualize_text_regions(image_bytes: bytes, regions: List[Tuple[int, int, int, int]]) -> bytes:
    """
    Создает визуализацию найденных текстовых регионов.
    OpenCV загружается только при вызове этой функции.
    """
    if not check_opencv_availability():
        print("❌ OpenCV недоступен, возвращаем пустые байты")
        return b''
    
    try:
        with OpenCVContext() as cv2:
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
