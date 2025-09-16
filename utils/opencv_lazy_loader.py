"""
Ленивый загрузчик OpenCV для оптимизации производительности
Загружает OpenCV только при необходимости и выгружает после использования
"""
import sys
import gc
from typing import Optional, Any
import warnings

# Глобальная переменная для отслеживания загруженного OpenCV
_cv2_module: Optional[Any] = None
_opencv_loaded = False

def get_opencv():
    """
    Ленивая загрузка OpenCV - загружает модуль только при первом вызове
    """
    global _cv2_module, _opencv_loaded
    
    if not _opencv_loaded:
        try:
            print("🔍 Загружаем OpenCV для анализа изображения...")
            import cv2
            _cv2_module = cv2
            _opencv_loaded = True
            print("✅ OpenCV загружен успешно")
        except ImportError as e:
            print(f"❌ Ошибка загрузки OpenCV: {e}")
            raise
        except Exception as e:
            print(f"❌ Неожиданная ошибка при загрузке OpenCV: {e}")
            raise
    
    return _cv2_module

def unload_opencv():
    """
    Выгружает OpenCV из памяти для освобождения ресурсов
    """
    global _cv2_module, _opencv_loaded
    
    if _opencv_loaded and _cv2_module is not None:
        try:
            print("🧹 Выгружаем OpenCV из памяти...")
            
            # Очищаем кэш OpenCV (если доступно)
            try:
                if hasattr(_cv2_module, 'destroyAllWindows'):
                    _cv2_module.destroyAllWindows()
            except Exception:
                # Игнорируем ошибки destroyAllWindows (не критично)
                pass
            
            # Удаляем модуль из sys.modules
            if 'cv2' in sys.modules:
                del sys.modules['cv2']
            
            # Очищаем глобальную переменную
            _cv2_module = None
            _opencv_loaded = False
            
            # Принудительная сборка мусора
            gc.collect()
            
            print("✅ OpenCV выгружен из памяти")
            
        except Exception as e:
            print(f"⚠️ Ошибка при выгрузке OpenCV: {e}")
            # Не поднимаем исключение - это не критично

def is_opencv_loaded() -> bool:
    """
    Проверяет, загружен ли OpenCV
    """
    return _opencv_loaded and _cv2_module is not None

def with_opencv(func):
    """
    Декоратор для функций, которые используют OpenCV
    Автоматически загружает OpenCV перед выполнением и выгружает после
    """
    def wrapper(*args, **kwargs):
        # Загружаем OpenCV
        cv2 = get_opencv()
        
        try:
            # Выполняем функцию
            result = func(cv2, *args, **kwargs)
            return result
        finally:
            # Выгружаем OpenCV после выполнения
            unload_opencv()
    
    return wrapper

def with_opencv_async(func):
    """
    Асинхронный декоратор для функций, которые используют OpenCV
    """
    async def wrapper(*args, **kwargs):
        # Загружаем OpenCV
        cv2 = get_opencv()
        
        try:
            # Выполняем асинхронную функцию
            result = await func(cv2, *args, **kwargs)
            return result
        finally:
            # Выгружаем OpenCV после выполнения
            unload_opencv()
    
    return wrapper

class OpenCVContext:
    """
    Контекстный менеджер для работы с OpenCV
    Автоматически загружает и выгружает OpenCV
    """
    
    def __init__(self):
        self.cv2 = None
    
    def __enter__(self):
        self.cv2 = get_opencv()
        return self.cv2
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        unload_opencv()
        return False  # Не подавляем исключения

# Функция для проверки доступности OpenCV без загрузки
def check_opencv_availability() -> bool:
    """
    Проверяет доступность OpenCV без его загрузки
    """
    try:
        import importlib.util
        spec = importlib.util.find_spec("cv2")
        return spec is not None
    except Exception:
        return False
