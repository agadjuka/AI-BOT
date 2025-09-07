#!/usr/bin/env python3
"""
Simple import test to diagnose hanging issues
"""

print("Starting simple import test...")

try:
    print("1. Testing basic imports...")
    import os
    import sys
    print("✅ Basic imports successful")
except Exception as e:
    print(f"❌ Basic imports failed: {e}")

try:
    print("2. Testing config import...")
    from config.settings import BotConfig
    print("✅ Config import successful")
except Exception as e:
    print(f"❌ Config import failed: {e}")

try:
    print("3. Testing poster_handler import...")
    from poster_handler import get_all_poster_ingredients
    print("✅ poster_handler import successful")
except Exception as e:
    print(f"❌ poster_handler import failed: {e}")

try:
    print("4. Testing google_sheets_handler import...")
    from google_sheets_handler import get_google_sheets_ingredients
    print("✅ google_sheets_handler import successful")
except Exception as e:
    print(f"❌ google_sheets_handler import failed: {e}")

print("Simple import test completed!")
