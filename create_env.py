#!/usr/bin/env python3
"""Создание .env файла с правильной кодировкой"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write('BOT_TOKEN=8351394597:AAE9aV6X4c0iLcRMqd_i4viccm_KCLdWStU\n')
    f.write('PROJECT_ID=just-advice-470905\n')
    f.write('GEMINI_ANALYSIS_MODE=production\n')

print('✅ Файл .env создан успешно')
