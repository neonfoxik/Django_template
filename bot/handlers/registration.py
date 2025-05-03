from bot.models import User, AvitoAccount, UserAvitoAccount
from bot import bot
from django.conf import settings
from bot.services import get_access_token, get_avito_user_id


def start_registration(message):
    """ Функция для отображения информации о боте """
    chat_id = message.chat.id
    
    # Проверяем, является ли чат группой (chat_id < 0 для групп)
    if chat_id < 0:
        bot.send_message(
            chat_id=chat_id, 
            text=f"Этот бот для получения статистики авито аккаунта.\n\n"
                 f"ID этой группы: {chat_id}\n"
                 f"Укажите этот ID в поле daily_report_tg_id или weekly_report_tg_id аккаунта Авито "
                 f"через админ-панель, чтобы получать отчеты в эту группу.\n\n"
                 f"Используйте команды:\n"
                 f"/daily - получить ежедневный отчет\n"
                 f"/weekly - получить еженедельный отчет"
        )
    else:
        # Для личных чатов
        bot.send_message(
            chat_id=chat_id, 
            text=f"Этот бот для получения статистики авито аккаунта.\n\n"
                 f"Ваш ID: {message.from_user.id}\n"
                 f"Укажите этот ID в поле daily_report_tg_id или weekly_report_tg_id аккаунта Авито "
                 f"через админ-панель, чтобы получать отчеты.\n\n"
                 f"Используйте команды:\n"
                 f"/daily - получить ежедневный отчет\n"
                 f"/weekly - получить еженедельный отчет"
        )


def start_avito_account_registration(message):
    """ Запускает процесс добавления аккаунта Авито """
    mesg = bot.send_message(message.chat.id, 'Введите название для аккаунта Авито (например, "Основной", "Работа" и т.д.)')
    bot.register_next_step_handler(mesg, get_account_name)


def get_account_name(message):
    account_name = message.text.strip()
    mesg = bot.send_message(message.chat.id, 'Введите Client ID Авито')
    bot.register_next_step_handler(mesg, lambda m: get_user_client_id(m, account_name))


def get_user_client_id(message, account_name):
    client_id = message.text.strip()
    mesg = bot.send_message(message.chat.id, 'Введите Client Secret Авито')
    bot.register_next_step_handler(mesg, lambda m: get_user_client_secret(m, account_name, client_id))


def get_user_client_secret(message, account_name, client_id):
    client_secret = message.text.strip()
    user_id = message.from_user.id
    
    # Пытаемся получить токен доступа
    token = get_access_token(client_id, client_secret)
    if not token:
        mesg = bot.send_message(
            chat_id=user_id, 
            text="❌ Ошибка: Не удалось получить токен доступа. Проверьте правильность Client Secret и введите его снова:"
        )
        bot.register_next_step_handler(mesg, lambda m: get_user_client_secret(m, account_name, client_id))
        return
    
    try:
        # Пытаемся получить Avito ID пользователя для проверки корректности данных
        avito_user_id = get_avito_user_id(client_id, client_secret)
        if not avito_user_id:
            mesg = bot.send_message(
                chat_id=user_id, 
                text="❌ Ошибка: Не удалось получить ID пользователя Авито. Проверьте правильность Client ID и Secret."
            )
            bot.register_next_step_handler(mesg, lambda m: get_user_client_secret(m, account_name, client_id))
            return
        
        # Спрашиваем, куда отправлять дневные отчеты
        mesg = bot.send_message(
            chat_id=user_id,
            text="Введите Telegram ID для отправки ежедневных отчетов (или оставьте пустым, чтобы использовать ваш ID)"
        )
        bot.register_next_step_handler(mesg, lambda m: get_daily_report_id(m, account_name, client_id, client_secret))
        
    except Exception as e:
        bot.send_message(
            chat_id=user_id, 
            text=f"❌ Ошибка при создании аккаунта: {str(e)}\nПопробуйте позже."
        )


def get_daily_report_id(message, account_name, client_id, client_secret):
    daily_report_tg_id = message.text.strip()
    user_id = message.from_user.id
    
    # Если поле пустое, используем ID пользователя
    if not daily_report_tg_id:
        daily_report_tg_id = str(user_id)
    
    # Спрашиваем, куда отправлять недельные отчеты
    mesg = bot.send_message(
        chat_id=user_id,
        text="Введите Telegram ID для отправки еженедельных отчетов (или оставьте пустым, чтобы использовать ваш ID)"
    )
    bot.register_next_step_handler(
        mesg, 
        lambda m: get_weekly_report_id(m, account_name, client_id, client_secret, daily_report_tg_id)
    )


def get_weekly_report_id(message, account_name, client_id, client_secret, daily_report_tg_id):
    from bot.handlers.common import menu_m
    
    weekly_report_tg_id = message.text.strip()
    user_id = message.from_user.id
    
    # Если поле пустое, используем ID пользователя
    if not weekly_report_tg_id:
        weekly_report_tg_id = str(user_id)
    
    try:
        user = User.objects.get(telegram_id=user_id)
        
        # Создаем аккаунт Авито
        avito_account = AvitoAccount.objects.create(
            name=account_name,
            client_id=client_id,
            client_secret=client_secret,
            daily_report_tg_id=daily_report_tg_id,
            weekly_report_tg_id=weekly_report_tg_id
        )
        
        # Связываем пользователя с аккаунтом Авито
        UserAvitoAccount.objects.create(
            user=user,
            avito_account=avito_account
        )
        
        bot.send_message(
            chat_id=user_id, 
            text=f"✅ Аккаунт Авито '{account_name}' успешно добавлен!\n\nТеперь вы можете получать отчеты."
        )
        menu_m(message)
    except Exception as e:
        bot.send_message(
            chat_id=user_id, 
            text=f"❌ Ошибка при создании аккаунта: {str(e)}\nПопробуйте позже."
        )


def add_avito_account(message):
    """ Функция для добавления дополнительного аккаунта Авито """
    user_id = message.from_user.id
    
    # Проверяем, что пользователь зарегистрирован
    user = User.objects.filter(telegram_id=user_id)
    if not user.exists():
        bot.send_message(
            chat_id=user_id,
            text="❌ Сначала необходимо зарегистрироваться. Используйте команду /start"
        )
        return
    
    # Начинаем процесс добавления аккаунта
    start_avito_account_registration(message)