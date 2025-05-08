from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot, logger
from bot.models import User
from bot.statistics import get_daily_statistics, get_weekly_statistics
from bot.handlers.common import format_expenses_message, format_report_message


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
    
    # Отправляем сообщение о загрузке и сохраняем его ID
    loading_message = bot.send_message(chat_id, "⏳ Получаем данные из API Авито...")
    
    try:
        user = User.objects.get(telegram_id=user_id)
        client_id = user.client_id
        client_secret = user.client_secret
        response = get_daily_statistics(client_id, client_secret)
        
        # Удаляем сообщение о загрузке после получения данных
        bot.delete_message(chat_id, loading_message.message_id)
        
        # Используем новую функцию форматирования отчета с префиксом имени пользователя
        message_text = f"👤 *{user.user_name}*\n\n" + format_report_message(response, user.user_name, is_weekly=False)
        
        bot.send_message(chat_id, message_text)
        
    except User.DoesNotExist:
        # Удаляем сообщение о загрузке в случае ошибки
        bot.delete_message(chat_id, loading_message.message_id)
        bot.send_message(chat_id, "❌ Ошибка: пользователь не найден.")
    except Exception as e:
        # Удаляем сообщение о загрузке в случае ошибки
        try:
            bot.delete_message(chat_id, loading_message.message_id)
        except:
            pass
        logger.error(f"Ошибка при получении отчета: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")