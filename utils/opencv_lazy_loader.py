"""
Ленивый загрузчик OpenCV для оптимизации производительности
Загружает OpenCV только при необходимости с полной изоляцией для параллельной обработки
"""
import sys
import gc
from typing import Optional, Any
import warnings

def get_opencv():
    """
    Ленивая загрузка OpenCV - создает новый экземпляр каждый раз для параллельной обработки
    """
    try:
        print("🔍 Загружаем OpenCV для анализа изображения...")
        import cv2
        print("✅ OpenCV загружен успешно")
        return cv2
    except ImportError as e:
        print(f"❌ Ошибка загрузки OpenCV: {e}")
        raise
    except Exception as e:
        print(f"❌ Неожиданная ошибка при загрузке OpenCV: {e}")
        raise

def unload_opencv():
    """
    Выгружает OpenCV из памяти для освобождения ресурсов
    """
    try:
        print("🧹 Выгружаем OpenCV из памяти...")
        
        # Очищаем кэш OpenCV (если доступно)
        try:
            if 'cv2' in sys.modules:
                cv2_module = sys.modules['cv2']
                if hasattr(cv2_module, 'destroyAllWindows'):
                    cv2_module.destroyAllWindows()
        except Exception:
            # Игнорируем ошибки destroyAllWindows (не критично)
            pass
        
        # Удаляем модуль из sys.modules
        if 'cv2' in sys.modules:
            del sys.modules['cv2']
        
        # Принудительная сборка мусора
        gc.collect()
        
        print("✅ OpenCV выгружен из памяти")
        
    except Exception as e:
        print(f"⚠️ Ошибка при выгрузке OpenCV: {e}")
        # Не поднимаем исключение - это не критично

def is_opencv_loaded() -> bool:
    """
    Проверяет, загружен ли OpenCV в sys.modules
    """
    return 'cv2' in sys.modules

def with_opencv(func):
    """
    Декоратор для функций, которые используют OpenCV
    Автоматически загружает OpenCV перед выполнением и выгружает после
    """
    def wrapper(*args, **kwargs):
        # Загружаем OpenCV (создает новый экземпляр)
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
        # Загружаем OpenCV (создает новый экземпляр)
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
    Автоматически загружает и выгружает OpenCV с полной изоляцией для параллельной обработки
    """
    
    def __init__(self):
        self.cv2 = None
        self._is_loaded = False
    
    def __enter__(self):
        # Загружаем OpenCV для этого конкретного контекста
        try:
            print("🔍 Загружаем OpenCV для анализа изображения...")
            import cv2
            self.cv2 = cv2
            self._is_loaded = True
            print("✅ OpenCV загружен успешно")
        except ImportError as e:
            print(f"❌ Ошибка загрузки OpenCV: {e}")
            raise
        except Exception as e:
            print(f"❌ Неожиданная ошибка при загрузке OpenCV: {e}")
            raise
        return self.cv2
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Выгружаем OpenCV только если мы его загружали
        if self._is_loaded and self.cv2 is not None:
            try:
                print("🧹 Выгружаем OpenCV из памяти...")
                
                # Очищаем кэш OpenCV (если доступно)
                try:
                    if hasattr(self.cv2, 'destroyAllWindows'):
                        self.cv2.destroyAllWindows()
                except Exception:
                    # Игнорируем ошибки destroyAllWindows (не критично)
                    pass
                
                # Удаляем модуль из sys.modules
                if 'cv2' in sys.modules:
                    del sys.modules['cv2']
                
                # Очищаем локальную переменную
                self.cv2 = None
                self._is_loaded = False
                
                # Принудительная сборка мусора
                gc.collect()
                
                print("✅ OpenCV выгружен из памяти")
                
            except Exception as e:
                print(f"⚠️ Ошибка при выгрузке OpenCV: {e}")
                # Не поднимаем исключение - это не критично
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
