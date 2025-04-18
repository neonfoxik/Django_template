from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot, logger
from bot.models import User
from bot.services import get_daily_statistics, get_weekly_statistics


def get_users(message):
    """Получение списка пользователей"""
    users = User.objects.filter(client_id__isnull = False)
    markup = InlineKeyboardMarkup()
    try:
        for user in users:
            btn = InlineKeyboardButton(text=user.user_name, callback_data=f"admin_{user.telegram_id}")
            markup.add(btn)
    except Exception as e:
        print(e)
    bot.send_message(text="Вот все пользователи:", chat_id=message.chat.id, reply_markup=markup)

def get_user_info(call):
    """Получение авито-статистики по пользователю"""
    chat_id = call.message.chat.id
    _, user_id = call.data.split("_")

    bot.send_message(chat_id, "⏳ Получаем данные из API Авито...")
    
    try:
        user = User.objects.get(telegram_id=user_id)
        client_id = user.client_id
        client_secret = user.client_secret
        response = get_daily_statistics(client_id, client_secret)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📊 *Статистика за {response['date']}*\n*👤 {user.user_name}*\n\n"
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