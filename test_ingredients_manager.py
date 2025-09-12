"""
Test script for IngredientsManager
Demonstrates usage of the ingredients management module
"""
import asyncio
from services.ingredients_manager import get_ingredients_manager


async def test_ingredients_manager():
    """Test the IngredientsManager functionality"""
    print("🧪 Testing IngredientsManager...")
    
    # Get the manager instance
    manager = get_ingredients_manager()
    
    # Test user ID
    test_user_id = 123456789
    
    print(f"\n1️⃣ Testing get_user_ingredients for user {test_user_id}...")
    ingredients = await manager.get_user_ingredients(test_user_id)
    print(f"   Current ingredients: {ingredients}")
    
    print(f"\n2️⃣ Testing update_user_ingredients for user {test_user_id}...")
    test_ingredients = ["Молоко", "Хлеб", "Яйца", "Масло"]
    success = await manager.update_user_ingredients(test_user_id, test_ingredients)
    print(f"   Update successful: {success}")
    
    print(f"\n3️⃣ Testing get_user_ingredients again...")
    ingredients = await manager.get_user_ingredients(test_user_id)
    print(f"   Updated ingredients: {ingredients}")
    
    print(f"\n4️⃣ Testing update with empty list...")
    success = await manager.update_user_ingredients(test_user_id, [])
    print(f"   Empty update successful: {success}")
    
    print(f"\n5️⃣ Testing get_user_ingredients after empty update...")
    ingredients = await manager.get_user_ingredients(test_user_id)
    print(f"   Ingredients after empty update: {ingredients}")
    
    print(f"\n6️⃣ Testing delete_user_ingredients...")
    success = await manager.delete_user_ingredients(test_user_id)
    print(f"   Delete successful: {success}")
    
    print(f"\n7️⃣ Testing get_user_ingredients after delete...")
    ingredients = await manager.get_user_ingredients(test_user_id)
    print(f"   Ingredients after delete: {ingredients}")
    
    print("\n✅ IngredientsManager test completed!")


if __name__ == "__main__":
    asyncio.run(test_ingredients_manager())
