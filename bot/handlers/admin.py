from telebot.types import InlineKeyboardButton, InlineKeyboardMarkup

from bot import bot, logger
from bot.models import User
from bot.services import get_daily_statistics, get_weekly_statistics
from bot.handlers.common import format_expenses_message


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
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📊 *Статистика за {response['date']}*\n*👤 {user.user_name}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:*\n"
        message_text += f"   • Всего: {response['chats']['total']}\n"
        message_text += f"   • Новых за день: {response['chats']['new']}\n"
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