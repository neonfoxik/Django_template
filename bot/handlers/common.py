from bot import bot
from bot.models import User
from bot.keyboards import main_markup
from bot.texts import MAIN_TEXT
from bot.services import AvitoApiService

import logging
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

logger = logging.getLogger(__name__)

def menu_m(message):
    """Главное меню"""
    chat_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    bot.send_message(
        chat_id=chat_id,
        text=MAIN_TEXT,
        reply_markup=main_markup
    )

def profile(call):
    """Отображение профиля пользователя и возможности обновить Client Secret"""
    user_id = call.from_user.id
    try:
        user = User.objects.get(telegram_id=user_id)
        
        # Если client_secret не установлен или установлен как none
        if not user.client_secret or user.client_secret == "none":
            markup = InlineKeyboardMarkup()
            btn_update = InlineKeyboardButton("Обновить Client Secret", callback_data="update_api_key")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_update).add(btn_back)
            
            bot.send_message(
                user_id, 
                "У вас не установлен Client Secret Авито. Нажмите кнопку, чтобы установить.",
                reply_markup=markup
            )
            return
        
        # Попробуем получить доступ к API, чтобы проверить валидность client_secret
        api_service = AvitoApiService(user.client_id, user.client_secret)
        profile_data = api_service.get_user_profile()
        
        # Создаем клавиатуру с кнопкой обновления client_secret
        markup = InlineKeyboardMarkup()
        btn_update = InlineKeyboardButton("Обновить Client Secret", callback_data="update_api_key")
        btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
        markup.add(btn_update).add(btn_back)
        
        # Если ошибка в получении профиля
        if "error" in profile_data:
            error_message = profile_data["error"]
            detailed_message = "Неверный Client Secret" if "token" in error_message.lower() else error_message
            
            bot.send_message(
                user_id, 
                f"⚠️ Ошибка при получении данных профиля: {detailed_message}\n\n"
                f"Ваш текущий Client Secret: `{user.client_secret[:5]}...{user.client_secret[-5:]}`\n\n"
                "Вы можете обновить Client Secret, нажав на кнопку ниже.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
            return
        
        # Формируем текст с информацией о профиле
        profile_text = "📋 Профиль Авито\n\n"
        profile_text += f"👤 Имя: {profile_data.get('name', 'Нет данных')}\n"
        profile_text += f"📧 Email: {profile_data.get('email', 'Нет данных')}\n"
        profile_text += f"📱 Телефон: {profile_data.get('phone', 'Нет данных')}\n"
        profile_text += f"🆔 ID: {profile_data.get('id', 'Нет данных')}\n\n"
        profile_text += f"🔑 Client Secret: `{user.client_secret[:5]}...{user.client_secret[-5:]}`"
        
        bot.send_message(user_id, profile_text, reply_markup=markup, parse_mode="Markdown")
    except User.DoesNotExist:
        bot.send_message(user_id, "Пользователь не найден. Введите /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при получении профиля: {e}")
        bot.send_message(user_id, f"Произошла ошибка: {e}")

def update_api_key(call):
    """Обновление Client Secret Авито"""
    user_id = call.from_user.id
    try:
        user = User.objects.get(telegram_id=user_id)
        mesg = bot.send_message(user_id, "Введите Client ID и Client Secret Авито через пробел (сначала Client ID, затем Client Secret):")
        bot.register_next_step_handler(mesg, save_new_api_key)
    except User.DoesNotExist:
        bot.send_message(user_id, "Пользователь не найден. Введите /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при обновлении Client Secret: {e}")
        bot.send_message(user_id, f"Произошла ошибка: {e}")

def save_new_api_key(message):
    """Сохранение нового Client Secret"""
    user_id = message.from_user.id
    try:
        credentials = message.text.strip().split()
        
        if len(credentials) != 2:
            markup = InlineKeyboardMarkup()
            btn_try_again = InlineKeyboardButton("Попробовать снова", callback_data="update_api_key")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_try_again).add(btn_back)
            
            bot.send_message(
                user_id, 
                "❌ Ошибка: Введите Client ID и Client Secret через пробел.",
                reply_markup=markup
            )
            return
        
        client_id, new_client_secret = credentials
        user = User.objects.get(telegram_id=user_id)
        
        # Проверяем валидность client_id и client_secret перед сохранением
        api_service = AvitoApiService(client_id=client_id, client_secret=new_client_secret)
        
        # Пытаемся получить токен доступа
        token = api_service.get_access_token()
        if not token:
            markup = InlineKeyboardMarkup()
            btn_try_again = InlineKeyboardButton("Попробовать снова", callback_data="update_api_key")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_try_again).add(btn_back)
            
            bot.send_message(
                user_id, 
                "❌ Ошибка: Не удалось получить токен доступа. Проверьте правильность Client ID и Client Secret.",
                reply_markup=markup
            )
            return
        
        # Если получение токена прошло успешно, пробуем получить данные пользователя
        profile_data = api_service.get_user_profile()
        
        if "error" in profile_data:
            error_message = profile_data["error"]
            detailed_message = "Неверные данные для аутентификации или ошибка доступа" if "token" in error_message.lower() else error_message
            
            markup = InlineKeyboardMarkup()
            btn_try_again = InlineKeyboardButton("Попробовать снова", callback_data="update_api_key")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_try_again).add(btn_back)
            
            bot.send_message(
                user_id, 
                f"❌ Ошибка: {detailed_message}\n\nДанные не сохранены. Проверьте данные и попробуйте снова.",
                reply_markup=markup
            )
            return
        
        # Если все проверки прошли успешно, сохраняем client_id и client_secret
        user.client_id = client_id
        user.client_secret = new_client_secret
        user.save()
        
        user_name = profile_data.get('name', 'пользователь')
        
        bot.send_message(
            user_id, 
            f"✅ Данные аутентификации Авито успешно обновлены!\n\nДобро пожаловать, {user_name}!\n\nТеперь вы можете использовать все функции бота.",
            reply_markup=main_markup
        )
    except User.DoesNotExist:
        bot.send_message(user_id, "Пользователь не найден. Введите /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при сохранении данных аутентификации: {e}")
        bot.send_message(user_id, f"Произошла ошибка: {e}")

def back_to_menu(call):
    """Возврат в главное меню"""
    user_id = call.from_user.id
    menu_message = {
        'chat': {'id': user_id},
        'from_user': {'id': user_id}
    }
    menu_m(menu_message)

def daily_report(call):
    """Отправка отчета за день"""
    user_id = call.from_user.id
    try:
        user = User.objects.get(telegram_id=user_id)
        
        if not user.client_secret or user.client_secret == "none":
            markup = InlineKeyboardMarkup()
            btn_update = InlineKeyboardButton("Обновить Client Secret", callback_data="update_api_key")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_update).add(btn_back)
            
            bot.send_message(
                user_id, 
                "⚠️ У вас не установлен Client Secret Авито. Нажмите кнопку, чтобы установить.",
                reply_markup=markup
            )
            return
        
        # Отправляем сообщение о загрузке данных
        wait_message = bot.send_message(user_id, "⏳ Загрузка данных...")
        
        api_service = AvitoApiService(user.client_id, user.client_secret)
        
        # Проверяем, можем ли получить токен доступа
        token = api_service.get_access_token()
        if not token:
            bot.delete_message(user_id, wait_message.message_id)
            
            markup = InlineKeyboardMarkup()
            btn_update = InlineKeyboardButton("Обновить Client Secret", callback_data="update_api_key")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_update).add(btn_back)
            
            bot.send_message(
                user_id, 
                "⚠️ Ошибка при получении токена доступа. Проверьте правильность Client Secret.",
                reply_markup=markup
            )
            return
        
        daily_stats = api_service.get_daily_statistics()
        
        # Проверяем наличие ошибок в данных
        has_error = False
        error_details = []
        
        for section_key in ['current', 'previous']:
            if section_key in daily_stats:
                data_section = daily_stats[section_key]
                for data_key, data_value in data_section.items():
                    if isinstance(data_value, dict) and "error" in data_value:
                        has_error = True
                        error_message = data_value["error"]
                        error_details.append(f"{data_key}: {error_message}")
                        logger.error(f"Ошибка при получении данных {data_key}: {error_message}")
        
        # Если есть ошибки в данных, показываем сообщение
        if has_error:
            bot.delete_message(user_id, wait_message.message_id)
            
            markup = InlineKeyboardMarkup()
            btn_update = InlineKeyboardButton("Обновить Client Secret", callback_data="update_api_key")
            btn_retry = InlineKeyboardButton("Повторить", callback_data="daily_report")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_retry).add(btn_update).add(btn_back)
            
            err_msg = "\n".join(error_details[:3]) if error_details else "Неизвестная ошибка API"
            
            bot.send_message(
                user_id, 
                f"⚠️ Произошла ошибка при получении данных от API Авито:\n\n"
                f"{err_msg}\n\n"
                "Возможные причины:\n"
                "- Неверный или истекший Client Secret\n"
                "- Сервер Авито временно недоступен\n"
                "- Недостаточно прав для получения данных\n\n"
                "Попробуйте обновить Client Secret или повторить запрос позже.",
                reply_markup=markup
            )
            return
        
        formatted_stats = api_service.format_daily_stats(daily_stats)
        
        # Удаляем сообщение о загрузке
        bot.delete_message(user_id, wait_message.message_id)
        
        bot.send_message(user_id, formatted_stats, reply_markup=main_markup)
    except User.DoesNotExist:
        bot.send_message(user_id, "Пользователь не найден. Введите /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при получении дневного отчета: {e}")
        bot.send_message(user_id, f"Произошла ошибка: {e}")

def weekly_report(call):
    """Отправка отчета за неделю"""
    user_id = call.from_user.id
    try:
        user = User.objects.get(telegram_id=user_id)
        
        if not user.client_secret or user.client_secret == "none":
            markup = InlineKeyboardMarkup()
            btn_update = InlineKeyboardButton("Обновить Client Secret", callback_data="update_api_key")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_update).add(btn_back)
            
            bot.send_message(
                user_id, 
                "⚠️ У вас не установлен Client Secret Авито. Нажмите кнопку, чтобы установить.",
                reply_markup=markup
            )
            return
        
        # Отправляем сообщение о загрузке данных
        wait_message = bot.send_message(user_id, "⏳ Загрузка данных...")
        
        api_service = AvitoApiService(user.client_id, user.client_secret)
        
        # Проверяем, можем ли получить токен доступа
        token = api_service.get_access_token()
        if not token:
            bot.delete_message(user_id, wait_message.message_id)
            
            markup = InlineKeyboardMarkup()
            btn_update = InlineKeyboardButton("Обновить Client Secret", callback_data="update_api_key")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_update).add(btn_back)
            
            bot.send_message(
                user_id, 
                "⚠️ Ошибка при получении токена доступа. Проверьте правильность Client Secret.",
                reply_markup=markup
            )
            return
        
        weekly_stats = api_service.get_weekly_statistics()
        
        # Проверяем наличие ошибок в данных
        has_error = False
        error_details = []
        
        for section_key in ['current', 'previous']:
            if section_key in weekly_stats:
                data_section = weekly_stats[section_key]
                for data_key, data_value in data_section.items():
                    if isinstance(data_value, dict) and "error" in data_value:
                        has_error = True
                        error_message = data_value["error"]
                        error_details.append(f"{data_key}: {error_message}")
                        logger.error(f"Ошибка при получении данных {data_key}: {error_message}")
        
        # Если есть ошибки в данных, показываем сообщение
        if has_error:
            bot.delete_message(user_id, wait_message.message_id)
            
            markup = InlineKeyboardMarkup()
            btn_update = InlineKeyboardButton("Обновить Client Secret", callback_data="update_api_key")
            btn_retry = InlineKeyboardButton("Повторить", callback_data="weekly_report")
            btn_back = InlineKeyboardButton("Назад", callback_data="back_to_menu")
            markup.add(btn_retry).add(btn_update).add(btn_back)
            
            err_msg = "\n".join(error_details[:3]) if error_details else "Неизвестная ошибка API"
            
            bot.send_message(
                user_id, 
                f"⚠️ Произошла ошибка при получении данных от API Авито:\n\n"
                f"{err_msg}\n\n"
                "Возможные причины:\n"
                "- Неверный или истекший Client Secret\n"
                "- Сервер Авито временно недоступен\n"
                "- Недостаточно прав для получения данных\n\n"
                "Попробуйте обновить Client Secret или повторить запрос позже.",
                reply_markup=markup
            )
            return
        
        formatted_stats = api_service.format_weekly_stats(weekly_stats)
        
        # Удаляем сообщение о загрузке
        bot.delete_message(user_id, wait_message.message_id)
        
        bot.send_message(user_id, formatted_stats, reply_markup=main_markup)
    except User.DoesNotExist:
        bot.send_message(user_id, "Пользователь не найден. Введите /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при получении недельного отчета: {e}")
        bot.send_message(user_id, f"Произошла ошибка: {e}")

# Обновляем главный обработчик для команды start
def start(message):
    """Обработчик команды /start"""
    from bot.handlers.registration import start_registration
    start_registration(message)
