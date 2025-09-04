# poster_handler.py

import requests
import json
from config.settings import POSTER_TOKEN

def get_all_poster_ingredients() -> dict:
    """
    Загружает все ингредиенты из Poster и возвращает словарь:
    {'название ингредиента в нижнем регистре': id}
    """
    api_url = f"https://joinposter.com/api/menu.getIngredients?token={POSTER_TOKEN}"
    print("Загружаю справочник ингредиентов из Join Poster...")
    
    try:
        response = requests.get(api_url)
        response.raise_for_status()  # Проверка на HTTP-ошибки
        ingredients_from_api = response.json().get("response", [])
        
        # Преобразуем список в удобный словарь для быстрого поиска
        ingredient_dictionary = {
            item['ingredient_name'].lower(): item['ingredient_id'] 
            for item in ingredients_from_api
        }
        
        print(f"✅ Успешно загружено {len(ingredient_dictionary)} ингредиентов.")
        return ingredient_dictionary
    except requests.exceptions.RequestException as e:
        print(f"❌ Ошибка при загрузке ингредиентов из Poster: {e}")
        return {}
    except json.JSONDecodeError:
        print("❌ Ошибка: не удалось расшифровать ответ от Poster. Возможно, неверный токен.")
        return {}
