from bot.models import User
from bot import bot
from django.conf import settings
from bot.services import get_access_token, get_avito_user_id


def start_registration(message):
    from bot.handlers.common import menu_m
    """ Функция для регистрации пользователей """
    user_id = message.from_user.id
    user = User.objects.filter(telegram_id=user_id)
    if user.exists():
        menu_m(message)
    else:
        mesg = bot.send_message(message.chat.id, 'Введите Client ID Авито')
        bot.register_next_step_handler(mesg, get_user_client_id)
        

def get_user_client_id(message):
    client_id = message.text.strip()
    mesg = bot.send_message(message.chat.id, 'Введите Client Secret Авито')
    bot.register_next_step_handler(mesg, lambda m: get_user_client_secret(m, client_id))

def get_user_client_secret(message, client_id):
    from bot.handlers.common import menu_m
    client_secret = message.text.strip()
    user_id = message.from_user.id
    
    # Пытаемся получить токен доступа
    token = get_access_token(client_id, client_secret)
    if not token:
        mesg = bot.send_message(
            chat_id=user_id, 
            text="❌ Ошибка: Не удалось получить токен доступа. Проверьте правильность Client Secret и введите его снова:"
        )
        bot.register_next_step_handler(mesg, lambda m: get_user_client_secret(m, client_id))
        return
    
    try:
        # Пытаемся получить Avito ID пользователя для проверки корректности данных
        avito_user_id = get_avito_user_id(client_id, client_secret)
        if not avito_user_id:
            mesg = bot.send_message(
                chat_id=user_id, 
                text="❌ Ошибка: Не удалось получить ID пользователя Авито. Проверьте правильность Client ID и Secret."
            )
            bot.register_next_step_handler(mesg, lambda m: get_user_client_secret(m, client_id))
            return
        
        # Создаем пользователя с проверенными учетными данными
        user = User.objects.create(
            telegram_id=user_id,
            user_name=message.from_user.first_name,
            client_id=client_id,
            client_secret=client_secret
        )
        user.save()
        
        user_name = message.from_user.first_name
        
        bot.send_message(
            chat_id=user_id, 
            text=f"✅ Client Secret Авито успешно сохранен!\n\nДобро пожаловать, {user_name}!"
        )
        menu_m(message)
    except Exception as e:
        bot.send_message(
            chat_id=user_id, 
            text=f"❌ Ошибка при создании пользователя: {str(e)}\nПопробуйте позже."
        )