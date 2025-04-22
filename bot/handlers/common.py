from bot import bot
from bot.models import User
from bot.keyboards import main_markup
from bot.texts import MAIN_TEXT
from bot.services import get_daily_statistics, get_weekly_statistics

import logging

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

def format_expenses_message(expenses):
    """Форматирует сообщение о расходах"""
    if not expenses:
        return "0.00 ₽"
        
    # Проверяем правильность структуры
    if not isinstance(expenses, dict):
        return "0.00 ₽"
        
    total = expenses.get('total', 0)
    details = expenses.get('details', {})
    
    if total <= 0:
        return "0.00 ₽"
    
    message = f"{total:.2f} ₽\n"
    
    # Добавляем детализацию расходов, если они есть
    if details:
        message += f"📋 *Детализация расходов:*\n"
        
        # Сортируем по убыванию суммы
        sorted_details = sorted(
            details.items(), 
            key=lambda x: x[1]['amount'], 
            reverse=True
        )
        
        for service, service_details in sorted_details:
            amount = service_details.get('amount', 0)
            count = service_details.get('count', 1)
            items = service_details.get('items', [])
            
            # Количество объявлений, если есть
            items_count = len(items) if items else 0
            items_suffix = ""
            if items_count > 0:
                items_suffix = f" ({items_count} объявл.)"
            
            message += f"   • {service}{items_suffix}: {amount:.2f} ₽ ({count} опер.)\n"
    
    return message

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
        
        message_text += f"💬 *Сообщения:*\n"
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
        
        message_text += f"💰 *Финансы:*\n"
        message_text += f"   • Реальный баланс: {response['balance_real']} ₽\n"
        message_text += f"   • Бонусы: {response['balance_bonus']} ₽\n"
        message_text += f"   • Аванс: {response['advance']} ₽\n\n"
        
        message_text += f"💸 *Расходы за сегодня:* "
        
        # Добавляем расходы и детализацию
        expenses_message = format_expenses_message(response.get('expenses', {}))
        message_text += expenses_message
        
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
        
        message_text += f"💬 *Сообщения:*\n"
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
        
        message_text += f"💰 *Финансы:*\n"
        message_text += f"   • Реальный баланс: {response['balance_real']} ₽\n"
        message_text += f"   • Бонусы: {response['balance_bonus']} ₽\n"
        message_text += f"   • Аванс: {response['advance']} ₽\n\n"
        
        message_text += f"💸 *Расходы за неделю:* "
        
        # Добавляем расходы и детализацию
        expenses_message = format_expenses_message(response.get('expenses', {}))
        message_text += expenses_message
        
        bot.send_message(chat_id, message_text, parse_mode="Markdown")
        
    except User.DoesNotExist:
        bot.send_message(chat_id, "❌ Ошибка: вы не зарегистрированы. Используйте /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при получении недельного отчета: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")

def send_daily_report(telegram_id):
    """Отправка дневного отчета по ID пользователя"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        client_id = user.client_id
        client_secret = user.client_secret
        response = get_daily_statistics(client_id, client_secret)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📊 *Статистика за {response['date']}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:*\n"
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
        
        message_text += f"💰 *Финансы:*\n"
        message_text += f"   • Реальный баланс: {response['balance_real']} ₽\n"
        message_text += f"   • Бонусы: {response['balance_bonus']} ₽\n"
        message_text += f"   • Аванс: {response['advance']} ₽\n\n"
        
        message_text += f"💸 *Расходы за сегодня:* "
        
        # Добавляем расходы и детализацию
        expenses_message = format_expenses_message(response.get('expenses', {}))
        message_text += expenses_message

        # Отправляем отчет на основной ID пользователя и на специальный ID для дневных отчетов, если он указан
        bot.send_message(telegram_id, message_text, parse_mode="Markdown")
        if user.daily_report_tg_id and user.daily_report_tg_id != telegram_id:
            bot.send_message(user.daily_report_tg_id, message_text, parse_mode="Markdown")
        
    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {telegram_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке дневного отчета: {e}")

def send_weekly_report(telegram_id):
    """Отправка недельного отчета по ID пользователя"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        client_id = user.client_id
        client_secret = user.client_secret
        response = get_weekly_statistics(client_id, client_secret)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📈 *Статистика за период: {response['period']}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:*\n"
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
        
        message_text += f"💰 *Финансы:*\n"
        message_text += f"   • Реальный баланс: {response['balance_real']} ₽\n"
        message_text += f"   • Бонусы: {response['balance_bonus']} ₽\n"
        message_text += f"   • Аванс: {response['advance']} ₽\n\n"
        
        message_text += f"💸 *Расходы за неделю:* "
        
        # Добавляем расходы и детализацию
        expenses_message = format_expenses_message(response.get('expenses', {}))
        message_text += expenses_message

        # Отправляем отчет на основной ID пользователя и на специальный ID для недельных отчетов, если он указан
        bot.send_message(telegram_id, message_text, parse_mode="Markdown")
        if user.weekly_report_tg_id and user.weekly_report_tg_id != telegram_id:
            bot.send_message(user.weekly_report_tg_id, message_text, parse_mode="Markdown")
        
    except User.DoesNotExist:
        logger.error(f"Пользователь с ID {telegram_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке недельного отчета: {e}")
