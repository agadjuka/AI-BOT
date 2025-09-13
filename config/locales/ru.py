"""
Русские тексты для Telegram бота
Содержит все тексты сообщений, кнопок, ошибок и уведомлений на русском языке
"""

RU_TRANSLATIONS = {
    # Приветственные сообщения
    "welcome": {
        "start_message": "Привет, {user}! 👋\n\nВыберите действие:",
        "analyze_receipt": "📸 Анализ чека\n\nОтправьте фото чека для анализа:",
        "main_menu": "🏠 Главное меню\n\nИспользуйте /start для начала новой работы.",
        "choose_language": "🌍 Выберите язык / Choose language:",
        "dashboard": {
            "welcome_message": "👤 Личный кабинет\n\nДобро пожаловать, {user}!\n\nВыберите настройку:",
            "buttons": {
                "language_settings": "🌍 Настройки языка",
                "google_sheets_management": "⚙️ Google Таблицы",
                "ingredients_management": "🥕 Список ингредиентов"
            }
        }
    },
    
    # Кнопки интерфейса
    "buttons": {
        # Основные действия
        "analyze_receipt": "📸 Анализировать чек",
        "back_to_receipt": "◀️ Вернуться к чеку",
        "back_to_main_menu": "◀️ Назад",
        "back": "⬅️ Назад",
        "dashboard": "👤 Личный кабинет",
        
        
        # Редактирование чека
        "add_row": "➕ Добавить строку",
        "delete_row": "➖ Удалить строку",
        "edit_line_number": "🔢 Редактировать строку по номеру",
        "edit_total": "💰 Редактировать Итого",
        "reanalyze": "🔄 Проанализировать заново",
        "upload_to_google_sheets": "📊 Загрузить в Google Таблицы",
        
        # Редактирование полей
        "edit_name": "📝 Название",
        "edit_quantity": "🔢 Количество", 
        "edit_price": "💰 Цена",
        "edit_total_field": "💵 Сумма",
        "apply_changes": "✅ Применить",
        "cancel": "❌ Отмена",
        "fix_line": "Исправить строку {line_number}",
        
        # Действия с итого
        "auto_calculate_total": "🧮 Рассчитать автоматически",
        "manual_edit_total": "✏️ Ввести вручную",
        
        # Статусы и действия
        "finish": "Отчет уже готов!",
        "noop": "Неизвестное действие"
    },
    
    # Сообщения об ошибках
    "errors": {
        "receipt_data_not_found": "❌ Данные чека не найдены",
        "operation_cancelled": "❌ Операция отменена\n\nИспользуйте /start для начала новой работы.",
        "unknown_action": "Неизвестное действие",
        "unsupported_language": "❌ Неподдерживаемый язык",
        "language_fallback": "❌ Неподдерживаемый язык. Установлен русский язык по умолчанию.",
        "field_not_specified": "❌ Ошибка: не указано поле для редактирования.\nПожалуйста, выберите поле для редактирования из меню.",
        "line_not_found": "Ошибка: строка не найдена",
        "data_not_found": "Произошла ошибка, данные не найдены.",
        "parsing_error": "Не удалось распознать структуру чека. Попробуйте сделать фото более четким.",
        "photo_processing_error": "Произошла ошибка при обработке фото: {error}",
        "field_edit_error": "Ошибка при редактировании поля: {error}",
        "total_update_error": "Ошибка при обновлении итоговой суммы: {error}",
        "total_update_retry": "Ошибка при обновлении итоговой суммы. Попробуйте еще раз.",
        "critical_photo_error": "❌ Критическая ошибка при обработке фото",
        "json_parsing_error": "Ошибка парсинга JSON или структуры данных от Gemini",
        "report_formation_error": "Ошибка при формировании отчета",
        "invalid_update_object": "Неверный объект обновления",
        "failed_to_edit_message": "Не удалось отредактировать сообщение {message_id}: {error}",
        "failed_to_delete_message": "Не удалось удалить сообщение {message_id}: {error}",
        "failed_to_delete_temporary_message": "Не удалось удалить временное сообщение {message_id}: {error}",
        "photos_already_processing": "❌ Фото уже обрабатываются. Пожалуйста, дождитесь завершения.",
        "too_many_photos": "❌ Слишком много фото. Максимум {max_photos} фото за раз.",
        "multiple_photos_error": "❌ Ошибка при обработке нескольких фото: {error}",
        "no_successful_photos": "❌ Ни одно фото не было обработано успешно. Попробуйте еще раз с более четкими фото.",
        "no_photos_in_group": "❌ В медиа-группе не найдено фото."
    },
    
    # Сообщения валидации
    "validation": {
        "line_number_too_small": "Номер строки должен быть больше 0",
        "line_number_too_large": "Номер строки {line_number} превышает максимальный {max_line_number}",
        "line_not_found": "Строка {line_number} не найдена",
        "field_negative": "{field_name} не может быть отрицательным",
        "invalid_line_format": "Неверный формат. Введите только номер строки (например: `3`):",
        "negative_value": "Значение не может быть отрицательным. Попробуйте еще раз.",
        "negative_total": "Итоговая сумма не может быть отрицательной. Попробуйте еще раз.",
        "try_again": "Попробуйте еще раз:",
        "no_items": "Нет товарных позиций",
        "incorrect_line_numbering": "Неправильная нумерация строк: {line_numbers}, ожидалось: {expected_numbers}",
        "missing_name_field": "Отсутствует поле name в строке {line_number}",
        "missing_status_field": "Отсутствует поле status в строке {line_number}",
        "missing_quantity_field": "Отсутствует поле quantity в строке {line_number}",
        "missing_price_field": "Отсутствует поле price в строке {line_number}",
        "missing_total_field": "Отсутствует поле total в строке {line_number}",
        "calculation_warning": "Предупреждение: Строка {line_number} - расчеты не сходятся: {quantity} * {price} = {expected_total}, но в чеке {total}",
        "data_correct": "Данные корректны",
        "line_number_correct": "Номер строки корректен",
        "field_cannot_be_empty": "{field_name} не может быть пустым",
        "invalid_numeric_format": "Неверный формат {field_name}. Введите число",
        "value_correct": "Значение корректно",
        "field_too_long": "{field_name} слишком длинное (максимум 100 символов)"
    },
    
    # Статусные сообщения
    "status": {
        "processing_receipt": "Обрабатываю квитанцию",
        "analyzing_receipt": "🔄 Анализирую фото заново...",
        "processing": "Обрабатываю...",
        "total_auto_calculated": "✅ Итого автоматически рассчитано: **{total}**",
        "line_deleted": "✅ Строка {line_number} удалена! Обновляю таблицу...",
        "total_updated": "✅ Итоговая сумма обновлена: **{total}**",
        "analysis_started": "🔍 Начинаем анализ чека...",
        "analysis_completed": "✅ Анализ завершен",
        "ingredients_loaded": "✅ Загружено {count} ингредиентов Google Sheets",
        "converted_to_receipt_data": "Данные конвертированы в ReceiptData",
        "data_saved": "Данные сохранены в user_data",
        "starting_analysis": "Начинаем анализ чека...",
        "processing_multiple_photos": "📸 Обрабатываю {total} фото... ({processed}/{total})",
        "processing_multiple_photos_progress": "📸 Обрабатываю фото...\n\n✅ Успешно: {successful}\n❌ Ошибок: {failed}\n📊 Прогресс: {processed}/{total}",
        "multiple_photos_completed": "✅ Обработка нескольких фото завершена!\n\n📊 Результаты:\n• Всего фото: {total}\n• Успешно: {successful}\n• Ошибок: {failed}"
    },
    
    # Сообщения анализа
    "analysis": {
        "errors_found": "🔴 **Обнаружены ошибки в данных чека**\n\n",
        "total_matches": "✅ **Итоговая сумма соответствует!**\n",
        "total_mismatch": "❗ **Несоответствие итоговой суммы! Разница: {difference}**\n",
        "auto_calculated": "*(автоматически рассчитана)*",
        "editing_line": "**Редактирование строки {line_number}:** {status_icon}\n\n",
        "editing_total": "**Редактирование итого:**\n\n",
        "current_total": "💰 **Текущая итоговая сумма:** {total}\n",
        "calculated_total": "🧮 **Автоматически рассчитанная сумма:** {calculated_total}\n\n",
        "choose_action": "Выберите действие:",
        "choose_field": "Выберите поле для редактирования:",
        "field_name": "📝 **Название:** {name}\n",
        "field_quantity": "🔢 **Количество:** {quantity}\n", 
        "field_price": "💰 **Цена:** {price}\n",
        "field_total": "💵 **Сумма:** {total}\n\n",
        "deleting_line": "🗑️ Удаление строки\n\nВведите номер строки для удаления:",
        "editing_line_input": "✏️ Редактирование строки\n\nВведите номер строки для редактирования:",
        "editing_total_input": "💰 Редактирование общей суммы\n\nВведите новую общую сумму:",
        "field_display_names": {
            "name": "название товара",
            "quantity": "количество", 
            "price": "цену",
            "total": "сумму"
        },
        "field_edit_input": "✏️ Редактирование {field_name} для строки {line_number}\n\nВведите новое значение:",
        "new_item_name": "Новый товар",
        "deleting_item_confirmation": "🗑️ Удаление позиции {item_number}\n\nПодтвердите удаление (да/нет):"
    },
    
    # Сообщения сопоставления ингредиентов
    "matching": {
        "no_ingredients": "Нет ингредиентов для сопоставления.",
        "matching_title": "**Сопоставление ингредиентов:**\n",
        "statistics": "📊 **Статистика:** Всего: {total} | 🟢 Точных: {exact} | 🟡 Частичных: {partial} | 🔴 Не найдено: {none}\n",
        "table_header": "{'№':<2} | {'Товар':<{name_width}} | {'Google Sheets':<{name_width}} | {'Статус':<4}",
        "manual_instructions": "**Инструкции по ручному сопоставлению:**\n\n1. Выберите номер предложения для автоматического сопоставления\n2. Или введите '0' для пропуска этого ингредиента\n3. Или введите 'search: <название>' для поиска других вариантов\n\nПримеры:\n• `1` - выбрать первое предложение\n• `0` - пропустить\n• `search: tomato` - найти варианты с 'tomato'",
        "no_search_results": "По запросу '{query}' ничего не найдено.",
        "search_results": "**Результаты поиска для '{query}':**\n",
        
        # Сообщения обработки ввода
        "matching_data_not_found": "Ошибка: данные сопоставления не найдены.",
        "failed_to_delete_message": "Не удалось удалить сообщение пользователя: {error}",
        "enter_search_query": "Введите поисковый запрос после 'search:'",
        "ingredient_skipped": "✅ Пропущен ингредиент: {ingredient_name}",
        "ingredient_matched": "✅ Сопоставлено: {receipt_item} → {matched_ingredient}",
        "invalid_suggestion_number": "Неверный номер. Введите число от 1 до {max_number} или 0 для пропуска.",
        "invalid_format": "Неверный формат. Введите номер предложения, 0 для пропуска или 'search: запрос' для поиска.",
        "processing_error": "Ошибка при обработке ручного сопоставления: {error}",
        "try_again": "Произошла ошибка. Попробуйте еще раз.",
        
        # Сообщения поиска
        "search_results_title": "**Результаты поиска для '{query}':**\n\n",
        "found_variants": "Найдено вариантов: **{count}**\n\n",
        "select_ingredient": "**Выберите ингредиент для сопоставления:**\n",
        "no_suitable_variants": "❌ **По запросу '{query}' не найдено подходящих вариантов**\n\nПопробуйте другой поисковый запрос или вернитесь к обзору.",
        "nothing_found": "❌ **По запросу '{query}' ничего не найдено**\n\nПопробуйте другой поисковый запрос или вернитесь к обзору.",
        "no_suitable_results": "По запросу '{query}' не найдено подходящих вариантов (с вероятностью > 50%).",
        "search_nothing_found": "По запросу '{query}' ничего не найдено.",
        
        # Кнопки поиска
        "new_search": "🔍 Новый поиск",
        "back_to_receipt": "📋 Назад к обзору",
        "skip_ingredient": "⏭️ Пропустить",
        "back": "◀️ Назад",
        
        # Сообщения позиционного сопоставления
        "invalid_line_number": "Неверный номер строки. Введите число от 1 до {max_lines}",
        "line_selected": "Выбрана строка {line_number}. Теперь введите название ингредиента из Google Sheets для поиска:",
        "invalid_line_format": "Неверный формат. Введите только номер строки (например: `3`):",
        
        # Прогресс сопоставления
        "matching_progress": "**Сопоставление ингредиентов** ({current}/{total})\n\n",
        "current_item": "**Текущий товар:** {item_name}\n\n",
        "auto_matched": "✅ **Автоматически сопоставлено:** {ingredient_name}\n\n",
        "continue_instruction": "Нажмите /continue для перехода к следующему товару.",
        
        # Финальный результат
        "rematch_ingredients": "🔄 Сопоставить заново",
        "back_to_receipt_final": "📋 Вернуться к чеку",
        
        # Callback сообщения для сопоставления ингредиентов
        "callback": {
            "results_not_found": "❌ Результаты сопоставления не найдены",
            "manual_matching": "✏️ Ручное сопоставление",
            "show_table": "📊 Показать таблицу",
            "back_to_edit": "◀️ Назад",
            "auto_match_all": "🔄 Автоматическое сопоставление",
            "matching_overview_title": "🔍 **Обзор сопоставления ингредиентов**\n\n",
            "statistics_title": "📊 **Статистика:**\n",
            "matched_count": "✅ Сопоставлено: {count}\n",
            "partial_count": "⚠️ Частично: {count}\n",
            "no_match_count": "❌ Не сопоставлено: {count}\n",
            "total_positions": "📝 Всего позиций: {count}\n\n",
            "choose_action": "Выберите действие:",
            "position_selection_title": "🔍 **Выберите позицию для сопоставления:**\n\n",
            "invalid_position_index": "❌ Неверный индекс позиции",
            "invalid_suggestion_number": "❌ Неверный номер предложения",
            "matching_position_title": "🔍 **Сопоставление позиции {position}:**\n\n",
            "receipt_item": "📝 **Товар из чека:** {item_name}\n\n",
            "suggestions_title": "💡 **Предложения:**\n",
            "no_suggestions": "❌ Предложения не найдены\n",
            "manual_search": "🔍 Поиск вручную",
            "skip_item": "❌ Пропустить",
            "back_to_list": "◀️ Назад к списку",
            "matching_completed": "✅ **Сопоставление выполнено!**\n\n",
            "matched_item": "📝 **Товар:** {item_name}\n",
            "matched_ingredient": "🎯 **Ингредиент:** {ingredient_name}\n",
            "similarity_score": "📊 **Сходство:** {score:.2f}\n\n",
            "continue_to_next": "Переходим к следующей позиции...",
            "next_position": "➡️ Следующая позиция",
            "matching_finished": "🎉 **Сопоставление завершено!**\n\n",
            "results_title": "📊 **Результаты:**\n",
            "matched_percentage": "📈 Процент: {percentage:.1f}%\n\n",
            "all_matched": "🎯 Все позиции успешно сопоставлены!",
            "remaining_items": "⚠️ Осталось сопоставить: {count} позиций",
            "back_to_editing": "◀️ Назад к редактированию",
            "changes_applied": "✅ Изменения сопоставления применены!\n\nПереходим к следующему шагу...",
            "search_ingredient": "🔍 Поиск ингредиента\n\nВведите название ингредиента для поиска:",
            "back_without_changes": "✅ Возврат без сохранения изменений\n\nИзменения не были сохранены.",
            "cancel_back": "❌ Отмена возврата\n\nПродолжаем работу с текущими данными."
        }
    },
    
    # Сообщения управления Google Таблицами
    "sheets_management": {
        "title": "📊 Управление Google Таблицами",
        "no_sheets_description": "У вас еще не подключено ни одной таблицы. Давайте добавим первую!",
        "has_sheets_description": "Вот ваши подключенные таблицы. Таблица со звездочкой (⭐) используется по умолчанию для загрузки чеков.",
        "add_new_sheet_instruction": "📊 **Добавить новую Google Таблицу**\n\nЭта функция скоро появится! Здесь вы сможете добавлять и настраивать свои Google Таблицы.",
        "buttons": {
            "add_new_sheet": "➕ Добавить новую таблицу",
            "back_to_dashboard": "⬅️ Назад"
        }
    },
    
    # Сообщения управления ингредиентами
    "ingredients": {
        "management": {
            "no_ingredients": "🥕 Управление списком ингредиентов\n\nУ вас пока нет персонального списка ингредиентов. Этот список используется для более точного распознавания позиций в чеках.\n\nВы можете загрузить свой список в виде простого текстового файла (.txt) или отправить список в текстовом сообщении, где каждый ингредиент написан с новой строки.",
            "has_ingredients": "🥕 Управление списком ингредиентов\n\nУ вас загружен персональный список. Он используется для сопоставления позиций в чеках.",
            "list_display": "🥕 Ваш список ингредиентов\n\n{ingredients}\n\nВыберите действие:",
            "replace_instruction": "🔄 Замена списка ингредиентов\n\nОтправьте новый текстовый файл (.txt) с ингредиентами, где каждый ингредиент написан с новой строки.\n\nЭтот файл заменит ваш текущий список.",
            "file_upload_instruction": "📥 Загрузка файла с ингредиентами\n\nОтправьте текстовый файл (.txt) с ингредиентами, где каждый ингредиент написан с новой строки.\n\nПример содержимого файла:\nМолоко\nХлеб\nЯйца\nМасло",
            "file_upload_request": "Пожалуйста, отправьте мне текстовый файл (.txt) со списком ваших ингредиентов. Каждый ингредиент должен быть на новой строке.",
            "text_upload_request": "📝 Загрузка списка из текста\n\nОтправьте список ингредиентов в текстовом сообщении, где каждый ингредиент написан с новой строки.\n\nПример:\nМолоко\nХлеб\nЯйца\nМасло",
            "text_upload_success": "✅ Список из {count} ингредиентов успешно загружен из текста!",
            "text_upload_error_empty": "Сообщение пусто или не содержит валидных ингредиентов.",
            "text_upload_error_processing": "Ошибка обработки текста. Попробуйте еще раз.",
            "file_upload_success": "✅ Список из {count} ингредиентов успешно загружен!",
            "file_upload_error_format": "Пожалуйста, отправьте файл в формате .txt.",
            "file_upload_error_empty": "Файл пуст или не содержит валидных ингредиентов.",
            "file_upload_error_processing": "Ошибка обработки файла. Попробуйте еще раз.",
            "delete_confirmation": "🗑️ Удаление списка ингредиентов\n\nВы уверены, что хотите удалить ваш персональный список ингредиентов?\n\nЭто действие нельзя отменить.",
            "delete_success": "✅ Список ингредиентов удален\n\nВаш персональный список ингредиентов был успешно удален.",
            "delete_error": "❌ Ошибка при удалении\n\nНе удалось удалить список ингредиентов. Попробуйте еще раз.",
            "buttons": {
                "upload_file": "📥 Загрузить файл",
                "upload_text": "📝 Загрузить из текста",
                "view_list": "📄 Посмотреть список",
                "replace_list": "🔄 Заменить список",
                "delete_list": "🗑️ Удалить список",
                "confirm_delete": "✅ Да, удалить",
                "cancel_delete": "❌ Отмена"
            }
        }
    },
    
    # Сообщения добавления новой таблицы
    "add_sheet": {
        "step1_title": "📄 Добавление таблицы (Шаг 1 из 3)",
        "step1_instruction": "Чтобы подключить таблицу, выполните следующие шаги:\n\n📝 1. Создайте новую Google Таблицу, либо используйте уже существующую (убедитесь что там нет конфиденциальной информации).\n\n🔗 2. Нажмите кнопку «Настройки доступа» в правом верхнем углу.\n\n📧 3. В поле «Добавьте пользователей и группы» вставьте этот email:\n\n<code>{service_email}</code>\n\n✅ 4. Убедитесь, что вы дали права <b>Редактора</b>.\n\n📋 5. Скопируйте ссылку на таблицу из браузера и отправьте ее мне следующим сообщением.",
        "step2_title": "📝 Придумайте имя (Шаг 2 из 3)",
        "step2_instruction": "✅ Отлично, доступ есть! Теперь придумайте для таблицы простое имя, чтобы не запутаться. Например: <i>Домашние расходы</i>.",
        "step3_title": "📊 Настройка таблицы: «{sheet_name}»",
        "step3_instruction": "Отлично! Таблица подключена. По умолчанию, данные будут записываться так:",
        "step3_question": "Использовать эти настройки или задать свои?",
        "table_headers": {
            "date": "Дата",
            "product": "Товар", 
            "quantity": "Кол",
            "price": "Цена",
            "sum": "Сумма"
        },
        "step3_success": "🎉 Таблица «{sheet_name}» успешно добавлена!",
        "buttons": {
            "cancel": "⬅️ Отмена",
            "use_default": "✅ Использовать по умолчанию",
            "configure_manual": "✏️ Настроить вручную"
        },
        "mapping_editor": {
            "title": "⚙️ **Редактор настроек таблицы**",
            "description": "Настройте соответствие полей чека и колонок в таблице:",
            "current_settings": "**Текущие настройки:**",
            "field_mapping": "{field_name} ➡️ Колонка {column}",
            "field_buttons": {
                "check_date": "🗓️ Текущая дата",
                "product_name": "📦 Название товара", 
                "quantity": "🔢 Количество",
                "price_per_item": "💰 Цена за единицу",
                "total_price": "💵 Общая цена"
            },
            "action_buttons": {
                "save_and_exit": "✅ Сохранить и выйти",
                "cancel": "⬅️ Отмена",
            },
            "column_input": "Укажите **новую колонку** для поля '{field_name}'.\n\nВы можете использовать любую колонку (например, <code>C</code> или <code>AA</code>). Чтобы не использовать это поле, просто отправьте <code>-</code> (дефис).",
            "field_names": {
                "check_date": "Текущая дата",
                "product_name": "Название товара",
                "quantity": "Количество", 
                "price_per_item": "Цена за единицу",
                "total_price": "Общая цена"
            },
            "errors": {
                "invalid_column": "❌ Неверный формат колонки. Введите букву (A-Z) или `-` для отключения.",
                "invalid_row_number": "❌ Неверный номер строки. Введите положительное число (например, `2`).",
                "no_field_selected": "❌ Не выбрано поле для редактирования."
            },
            "save_success_existing": "✅ **Настройки таблицы успешно обновлены!**\n\nВаши изменения сохранены и будут использоваться для будущих загрузок.",
            "save_success_new": "✅ **Таблица «{sheet_name}» успешно добавлена!**\n\nВаши пользовательские настройки сохранены и будут использоваться для будущих загрузок.",
            "save_error": "❌ **Ошибка сохранения настроек**\n\nПроизошла ошибка при сохранении настроек таблицы. Попробуйте еще раз.",
            "cancel_message": "❌ **Редактирование отменено**\n\nИзменения не были сохранены. Возвращаемся к управлению таблицами."
        },
        "errors": {
            "invalid_url": "🤔 Не могу получить доступ к таблице. Пожалуйста, дважды проверьте, что вы дали права <b>Редактора</b> именно для этого email. Попробуйте отправить ссылку еще раз.",
            "invalid_sheet_id": "❌ Не удалось извлечь ID таблицы из ссылки. Пожалуйста, отправьте корректную ссылку на Google Таблицу.",
            "save_failed": "⚠️ Ошибка при сохранении таблицы. Попробуйте еще раз.",
            "jwt_error": "⚠️ Проблема с проверкой доступа. Продолжаем процесс добавления таблицы."
        }
    },
    
    # Сообщения Google Sheets
    "sheets": {
        "ingredients_loaded": "✅ Загружено {count} ингредиентов Google Sheets по требованию",
        "no_data_for_upload": "❌ **Нет данных для загрузки**\n\nСначала необходимо загрузить и проанализировать чек.\nНажмите 'Анализировать чек' и загрузите фото чека.",
        "no_personal_ingredients": "❌ **Нет персональных ингредиентов**\n\nУ вас не загружен список ингредиентов для сопоставления.\nПожалуйста, сначала загрузите свой список ингредиентов в настройках.",
        
        # Сообщения поиска в Google Sheets
        "no_line_selected": "Ошибка: не выбрана строка для сопоставления.",
        "dictionary_not_loaded": "Ошибка: справочник Google Таблиц не загружен.",
        "no_search_results": "По запросу '{query}' в Google Таблицах ничего не найдено.",
        "no_item_selected": "Ошибка: не выбран товар для поиска.",
        "ingredients_loaded_for_search": "✅ Загружено {count} ингредиентов Google Sheets для поиска",
        "using_cached_ingredients": "✅ Используем уже загруженные {count} ингредиентов Google Sheets",
        "search_results_title": "**Результаты поиска в Google Таблицах для '{query}':**\n\n",
        "search_result_button": "{number}. {name}",
        "back_button": "◀️ Назад",
        
        # Callback сообщения для Google Sheets
        "callback": {
            "matching_results_not_found": "❌ Результаты сопоставления не найдены",
            "choose_action_for_matching": "Выберите действие для работы с сопоставлением:",
            "preview_data_not_found": "❌ Данные для предпросмотра не найдены",
            "upload_preview_title": "📊 **Предварительный просмотр загрузки в Google Таблицы**",
            "uploading_data": "📤 Загружаем данные в Google Sheets...",
            "receipt_data_not_found": "Данные чека не найдены",
            "upload_successful": "Загрузка успешна",
            "upload_error": "❌ Ошибка при загрузке: {message}",
            "no_sheet_configured": "❌ Не настроена Google Таблица\n\nПожалуйста, сначала настройте Google Таблицу в настройках бота.",
            "service_not_available": "❌ Сервис Google Sheets недоступен\n\nПроверьте настройки подключения.",
            "quota_exceeded": "⚠️ Превышена квота API Google Sheets\n\nПопробуйте загрузить данные позже. Система автоматически повторит попытку.",
            "permission_denied": "❌ Нет доступа к Google Таблице\n\nПроверьте права доступа сервисного аккаунта.",
            "sheet_not_found": "❌ Google Таблица не найдена\n\nПроверьте правильность ссылки на таблицу.",
            "matching_data_not_found": "Ошибка: данные для сопоставления не найдены.",
            "dictionary_not_loaded": "Не удалось загрузить справочник ингредиентов для Google Sheets.\nПроверьте настройки конфигурации.",
            "all_positions_processed": "✅ Все позиции обработаны!",
            "choose_position_for_matching": "**Выберите позицию для сопоставления**",
            "matching_updated": "✅ Сопоставление обновлено!",
            "data_successfully_uploaded": "✅ **Данные успешно загружены в Google Sheets!**",
            "no_upload_data_for_undo": "Нет данных о последней загрузке для отмены",
            "no_data_to_undo": "Нет данных для отмены",
            "undo_upload_failed": "Не удалось отменить загрузку: {message}",
            "unexpected_error": "❌ **Критическая ошибка**\n\nПроизошла неожиданная ошибка при загрузке в Google Sheets:\n`{error}`",
            "no_receipt_data_for_file": "❌ Нет данных чека для генерации файла.",
            "no_matching_data_for_file": "❌ Нет данных сопоставления Google Sheets для генерации файла.",
            "excel_generation_error": "❌ Ошибка при создании Excel файла.",
            "excel_generation_error_detailed": "❌ Ошибка при создании Excel файла: {error}",
            "matching_table_title": "**Сопоставление с ингредиентами Google Таблиц:**",
            "no_ingredients_for_matching": "Нет ингредиентов для сопоставления.",
            "table_header": "№ | Наименование            | Ингредиент          | Статус",
            "manual_matching_editor_title": "**Редактор сопоставления для Google Таблиц**",
            "current_item": "**Товар:** {item_name}",
            "choose_suitable_ingredient": "**Выберите подходящий ингредиент:**",
            "no_suitable_options": "❌ **Подходящих вариантов не найдено**",
            "undo_error_title": "❌ **{error_message}**",
            "undo_error_info": "Информация о последней загрузке не найдена.",
            "undo_successful": "✍️ **Загрузка успешно отменена!**",
            "cancelled_rows": "📊 **Отменено строк:** {row_count}",
            "worksheet_name": "📋 **Лист:** {worksheet_name}",
            "undo_time": "🕒 **Время отмены:** {time}",
            "data_deleted_from_sheets": "Данные были удалены из Google Sheets.",
            "no_data_for_preview": "❌ **Нет данных для предварительного просмотра**\n\nНе удалось найти данные чека для отображения предварительного просмотра Google Sheets.",
            "excel_file_created": "📄 **Excel-файл с данными чека создан!**",
            "excel_success_title": "✅ **Excel-файл успешно создан!**",
            "excel_success_description": "Файл содержит те же данные, что были загружены в Google Sheets.",
            "file_available_for_download": "⏰ **Файл будет доступен для скачивания в течение 5 минут**",
            "no_data_to_display": "Нет данных для отображения",
            "no_sheets_found": "❌ У вас нет подключенных таблиц",
            "no_sheet_selected": "❌ Таблица не выбрана",
            "sheet_not_found": "❌ Таблица не найдена",
            "switching_sheet": "🔄 Переключаем таблицу...",
            "date_header": "Date",
            "volume_header": "Vol",
            "price_header": "цена",
            "product_header": "Product",
            "total_label": "Итого:",
            "new_item_name": "Новый товар",
            "invalid_item_index": "Ошибка: неверный индекс товара.",
            "invalid_suggestion_index": "Ошибка: неверный индекс предложения.",
            "invalid_search_result_index": "Ошибка: неверный индекс результата поиска.",
            "matched_successfully": "✅ Сопоставлено: {receipt_item} → {ingredient_name}",
            "edit_matching": "✏️ Редактировать сопоставление",
            "preview": "👁️ Предпросмотр",
            "back_to_receipt": "◀️ Вернуться к чеку",
            "upload_to_google_sheets": "✅ Загрузить в Google Таблицы",
            "back": "◀️ Назад",
            "select_position_for_matching": "🔍 Выбрать позицию для сопоставления",
            "search": "🔍 Поиск",
            "undo_upload": "↩️ Отменить загрузку",
            "generate_file": "📄 Сгенерировать файл",
            "upload_new_receipt": "📸 Загрузить новый чек",
            "back_to_receipt_button": "📋 Вернуться к чеку",
            "preview_google_sheets": "👁️ Предпросмотр Google Sheets",
            "no_default_sheet_found": "❌ Не найдена основная таблица пользователя",
            "no_column_mapping_found": "❌ Не найден маппинг колонок для основной таблицы"
        }
    },
    
    # Сообщения файлов
    "files": {
        "no_data": "Нет данных для отображения",
        "table_header": "{'№':^{number_width}} | {'Товар':<{product_width}} | {'Кол':^{quantity_width}} | {'Цена':^{price_width}} | {'Сумма':>{total_width}} | {'':^{status_width}}",
        "total_label": "Итого:"
    },
    
    # Сообщения генерации файлов
    "file_generation": {
        "generating_file": "📄 Генерируем файл...",
        "file_ready": "📄 Файл для загрузки в {file_type} готов!",
        "success_title": "✅ **Файл {file_type} успешно сгенерирован!**",
        "filename": "📁 **Имя файла:** {filename}",
        "positions_count": "📊 **Позиций:** {count}",
        "generation_date": "📅 **Дата:** {date}",
        "show_table": "📊 Показать таблицу",
        "back_to_edit": "◀️ Назад к редактированию",
        "download_google_sheets_file": "📊 Скачать файл для Google Sheets",
        "matching_table_title": "📊 **Таблица сопоставления ингредиентов:**",
        "table_header": "| № | Товар из чека | Ингредиент | Статус | Сходство |",
        "table_separator": "|---|---|---|---|---|",
        "legend_title": "💡 **Легенда:**",
        "legend_matched": "✅ - Сопоставлено",
        "legend_partial": "⚠️ - Частично сопоставлено",
        "legend_not_matched": "❌ - Не сопоставлено",
        "not_matched": "Не сопоставлено",
        "error_generating_file": "❌ Ошибка при генерации файла: {error}",
        "google_sheets_handler_unavailable": "❌ Google Sheets handler not available for Excel generation",
        "ingredient_matching_handler_unavailable": "❌ Ingredient matching handler not available",
        "matching_results_not_found": "❌ Результаты сопоставления не найдены",
        "receipt_data_not_found": "❌ Данные чека не найдены"
    },
    
    # Общие сообщения и хелперы
    "common": {
        "no_data_to_display": "Нет данных для отображения",
        "page": "Страница {page}",
        "unknown_ingredient_type": "DEBUG: Неизвестный тип ингредиентов: {ingredient_type}",
        "loaded_google_sheets_ingredients": "✅ Загружено {count} ингредиентов Google Sheets по требованию",
        "debug_first_ingredients": "DEBUG: Первые 5 ингредиентов: {ingredients}",
        "navigation_buttons": {
            "first_page": "⏮️",
            "previous_page": "◀️", 
            "next_page": "▶️",
            "last_page": "⏭️"
        },
        "status_emojis": {
            "confirmed": "✅",
            "error": "🔴",
            "partial": "⚠️",
            "no_match": "❌",
            "exact_match": "🟢",
            "matched": "✅",
            "partial_match": "🟡",
            "unknown": "❓"
        }
    },
    
    # Сообщения форматирования
    "formatters": {
        "no_data_to_display": "Нет данных для отображения",
        "table_headers": {
            "number": "№",
            "product": "Товар",
            "quantity": "Кол",
            "price": "Цена",
            "amount": "Сумма"
        },
        "total_label": "Итого:"
    },
    
    # Настройки таблиц
    "table_settings": {
        "menu": {
            "title": "⚙️ **Настройки таблиц**\n\nНастройте отображение таблиц для вашего устройства",
            "ingredient_matching": "🔗 Сопоставление ингредиентов",
            "google_sheets": "📊 Google Таблицы",
            "receipt_preview": "👁️ Предпросмотр чека",
            "next_items": "⏭️ Следующие товары",
            "device_type": "📱 Тип устройства",
            "reset_all": "🔄 Сбросить все настройки"
        },
        "device_type": {
            "title": "**Настройки устройства**",
            "current_device": "Текущее устройство:",
            "mobile_description": "• **Мобильное** - компактные таблицы для маленьких экранов",
            "tablet_description": "• **Планшет** - средние таблицы для средних экранов",
            "desktop_description": "• **Десктоп** - полные таблицы для больших экранов"
        },
        "table_type": {
            "title": "**Настройки таблицы: {table_type}**",
            "device": "Устройство:",
            "max_length": "Максимальная длина названия:",
            "items_per_page": "Элементов на странице:",
            "compact_mode": "Компактный режим:",
            "emojis": "Показывать эмодзи:",
            "reset": "Сбросить к стандартным"
        },
        "values": {
            "yes": "Да",
            "no": "Нет",
            "mobile": "МОБИЛЬНОЕ",
            "tablet": "ПЛАНШЕТ",
            "desktop": "ДЕСКТОП"
        }
    },
    
    # Сообщения для таблиц
    "tables": {
        "no_data": {
            "ingredient_matching": "Нет ингредиентов для сопоставления.",
            "google_sheets_matching": "Нет ингредиентов для сопоставления с Google Таблицами.",
            "receipt_preview": "Нет данных для предпросмотра.",
            "next_items": "Нет следующих товаров.",
            "general": "Нет данных для отображения."
        }
    }
    
}