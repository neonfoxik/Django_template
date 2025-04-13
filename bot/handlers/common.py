from bot import bot
from bot.models import User
from bot.keyboards import main_markup
from bot.texts import MAIN_TEXT
from bot.services import get_daily_statistics, get_weekly_statistics

import logging
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
        message_text += f"   • С продвижением XL: {response['items']['with_xl_promotion']}\n\n"
        
        message_text += f"👁 *Просмотры:* {response['statistics']['views']}\n"
        message_text += f"📲 *Контакты:* {response['statistics']['contacts']}\n"
        message_text += f"❤️ *В избранном:* {response['statistics']['favorites']}\n\n"
        
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
        message_text += f"   • С продвижением XL: {response['items']['with_xl_promotion']}\n\n"
        
        message_text += f"👁 *Просмотры:* {response['statistics']['views']}\n"
        message_text += f"📲 *Контакты:* {response['statistics']['contacts']}\n"
        message_text += f"❤️ *В избранном:* {response['statistics']['favorites']}\n\n"
        
        message_text += f"💰 *Баланс:* {response['balance']} ₽"
        
        bot.send_message(chat_id, message_text, parse_mode="Markdown")
        
    except User.DoesNotExist:
        bot.send_message(chat_id, "❌ Ошибка: вы не зарегистрированы. Используйте /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при получении недельного отчета: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")
