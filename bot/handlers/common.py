from bot import bot
from bot.models import User, ItemData
from bot.keyboards import main_markup
from bot.texts import MAIN_TEXT
from bot.services import get_daily_statistics, get_weekly_statistics

import logging
import pandas as pd
import os
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

def start(message):
    """Обработчик команды /start"""
    from bot.handlers.registration import start_registration
    start_registration(message)

def menu_m(message):
    """Главное меню"""
    chat_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    bot.send_message(
        chat_id=chat_id,
        text=MAIN_TEXT,
        reply_markup=main_markup
    )

def daily_report(call):
    """Отправка дневного отчета пользователю"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id

    bot.send_message(chat_id, "⏳ Получаем данные из API Авито...")
    
    try:
        user = User.objects.get(telegram_id=user_id)
        client_id = user.client_id
        client_secret = user.client_secret
        response = get_daily_statistics(client_id, client_secret)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📊 *Статистика за {response['date']}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:* {response['chats']}\n"
        message_text += f"📱 *Показов телефона:* {response['phones_received']}\n\n"
        
        message_text += f"⭐ *Рейтинг:* {response['rating']}\n"
        message_text += f"👍 *Отзывы:*\n"
        message_text += f"   • Всего: {response['reviews']['total']}\n"
        message_text += f"   • За сегодня: {response['reviews']['today']}\n\n"
        
        message_text += f"📝 *Объявления:*\n"
        message_text += f"   • Всего: {response['items']['total']}\n"
        
        message_text += f"👁 *Просмотры:* {response['statistics']['views']}\n"
        message_text += f"📲 *Контакты:* {response['statistics']['contacts']}\n"
        message_text += f"❤️ *В избранном:* {response['statistics']['favorites']}\n\n"
        
        # Расчет расходов на основе данных о стоимости просмотров
        total_expense = calculate_expenses(user, response['statistics']['views'])
        if total_expense > 0:
            message_text += f"💸 *Расходы:* {total_expense:.2f} ₽\n\n"
        
        message_text += f"💰 *Баланс:* {response['balance']} ₽"
        
        bot.send_message(chat_id, message_text, parse_mode="Markdown")
        
    except User.DoesNotExist:
        bot.send_message(chat_id, "❌ Ошибка: вы не зарегистрированы. Используйте /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при получении дневного отчета: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")

def weekly_report(call):
    """Отправка недельного отчета пользователю"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    bot.send_message(chat_id, "⏳ Получаем данные из API Авито...")
    
    try:
        user = User.objects.get(telegram_id=user_id)
        client_id = user.client_id
        client_secret = user.client_secret
        response = get_weekly_statistics(client_id, client_secret)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📈 *Статистика за период: {response['period']}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:* {response['chats']}\n"
        message_text += f"📱 *Показов телефона:* {response['phones_received']}\n\n"
        
        message_text += f"⭐ *Рейтинг:* {response['rating']}\n"
        message_text += f"👍 *Отзывы:*\n"
        message_text += f"   • Всего: {response['reviews']['total']}\n"
        message_text += f"   • За неделю: {response['reviews']['weekly']}\n\n"
        
        message_text += f"📝 *Объявления:*\n"
        message_text += f"   • Всего: {response['items']['total']}\n"
        
        message_text += f"👁 *Просмотры:* {response['statistics']['views']}\n"
        message_text += f"📲 *Контакты:* {response['statistics']['contacts']}\n"
        message_text += f"❤️ *В избранном:* {response['statistics']['favorites']}\n\n"
        
        # Расчет расходов на основе данных о стоимости просмотров
        total_expense = calculate_expenses(user, response['statistics']['views'])
        if total_expense > 0:
            message_text += f"💸 *Расходы:* {total_expense:.2f} ₽\n\n"
        
        message_text += f"💰 *Баланс:* {response['balance']} ₽"
        
        bot.send_message(chat_id, message_text, parse_mode="Markdown")
        
    except User.DoesNotExist:
        bot.send_message(chat_id, "❌ Ошибка: вы не зарегистрированы. Используйте /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при получении недельного отчета: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")

def calculate_expenses(user, total_views):
    """Рассчитывает общие расходы на основе количества просмотров и стоимости предметов"""
    item_data_records = ItemData.objects.filter(user=user)
    
    if not item_data_records.exists() or total_views <= 0:
        return 0
    
    # Получаем только записи с положительной ценой
    valid_items = [item for item in item_data_records if item.view_price > 0]
    
    if not valid_items:
        return 0
    
    # Простое распределение просмотров между предметами
    item_count = len(valid_items)
    views_per_item = total_views / item_count if item_count > 0 else 0
    
    total_expense = 0
    for item_data in valid_items:
        total_expense += views_per_item * item_data.view_price
    
    return total_expense

def request_item_data_file(call):
    """Запрашивает у пользователя файл XLS с данными о предметах"""
    chat_id = call.message.chat.id
    
    msg = bot.send_message(
        chat_id=chat_id,
        text="Пожалуйста, отправьте XLS файл с данными о предметах.\n\n"
        "В столбце A должны быть ID предметов, а в столбце P - стоимость просмотра.",
        parse_mode="Markdown"
    )
    
    bot.register_next_step_handler(msg, process_item_data_file)

def process_item_data_file(message):
    """Обрабатывает полученный XLS файл с данными о предметах"""
    chat_id = message.chat.id
    user_id = message.from_user.id
    
    try:
        user = User.objects.get(telegram_id=user_id)
        
        # Проверяем, что сообщение содержит файл
        if not message.document:
            bot.send_message(chat_id, "❌ Ошибка: не обнаружен файл. Пожалуйста, отправьте XLS файл.")
            return
        
        # Проверяем тип файла
        file_info = bot.get_file(message.document.file_id)
        file_extension = os.path.splitext(message.document.file_name)[1].lower()
        
        if file_extension not in ['.xls', '.xlsx']:
            bot.send_message(chat_id, "❌ Ошибка: неверный формат файла. Пожалуйста, отправьте файл в формате XLS или XLSX.")
            return
        
        # Загружаем файл
        downloaded_file = bot.download_file(file_info.file_path)
        
        # Сохраняем файл временно
        temp_file_path = f"temp_{message.document.file_id}{file_extension}"
        with open(temp_file_path, 'wb') as temp_file:
            temp_file.write(downloaded_file)
        
        bot.send_message(chat_id, "⏳ Обрабатываем файл...")
        
        # Читаем файл с помощью pandas
        df = pd.read_excel(temp_file_path)
        
        # Проверяем наличие необходимых столбцов
        if 'A' not in df.columns or 'P' not in df.columns:
            if len(df.columns) > 0 and len(df.columns) > 15:  # Проверка на наличие достаточного количества столбцов
                # Предполагаем, что первый столбец - A, а 16-й столбец - P (нумерация с 0)
                item_id_column = df.columns[0]
                price_column = df.columns[15]
            else:
                bot.send_message(chat_id, "❌ Ошибка: в файле отсутствуют необходимые столбцы A и P.")
                os.remove(temp_file_path)
                return
        else:
            item_id_column = 'A'
            price_column = 'P'
        
        # Удаляем старые данные о предметах для пользователя
        ItemData.objects.filter(user=user).delete()
        
        # Счетчики для отчета
        added_count = 0
        skipped_count = 0
        
        # Обрабатываем данные
        for _, row in df.iterrows():
            item_id = str(row[item_id_column]).strip()
            try:
                price = float(row[price_column])
            except (ValueError, TypeError):
                price = 0
            
            if item_id and price > 0:
                # Используем update_or_create вместо create для предотвращения ошибок уникальности
                ItemData.objects.update_or_create(
                    user=user,
                    item_id=item_id,
                    defaults={'view_price': price}
                )
                added_count += 1
            else:
                skipped_count += 1
        
        # Удаляем временный файл
        os.remove(temp_file_path)
        
        bot.send_message(
            chat_id,
            f"✅ Файл успешно обработан!\n\n"
            f"📊 *Результаты:*\n"
            f"• Добавлено предметов: {added_count}\n"
            f"• Пропущено (цена = 0): {skipped_count}",
            parse_mode="Markdown"
        )
        
    except User.DoesNotExist:
        bot.send_message(chat_id, "❌ Ошибка: вы не зарегистрированы. Используйте /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при обработке файла с данными о предметах: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")
        try:
            # Пытаемся удалить временный файл в случае ошибки
            if 'temp_file_path' in locals():
                os.remove(temp_file_path)
        except:
            pass
