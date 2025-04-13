from bot.models import User
from bot import bot
from django.conf import settings


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
    
    # Проверяем валидность client_secret
    api_service = AvitoApiService(client_id, client_secret)
    
    # Пытаемся получить токен доступа
    token = api_service.get_access_token()
    if not token:
        mesg = bot.send_message(
            chat_id=user_id, 
            text="❌ Ошибка: Не удалось получить токен доступа. Проверьте правильность Client Secret и введите его снова:"
        )
        bot.register_next_step_handler(mesg, lambda m: get_user_client_secret(m, client_id))
        return
    
    # Создаем пользователя с проверенным client_secret
    user = User.objects.create(
        telegram_id=user_id,
        user_name=message.from_user.first_name,
        client_id=client_id,
        client_secret=client_secret
    )
    user.save()
    
    # Получаем имя пользователя из API, если возможно
    profile_data = api_service.get_user_profile()
    user_name = profile_data.get('name', 'пользователь') if isinstance(profile_data, dict) and 'name' in profile_data else 'пользователь'
    
    bot.send_message(
        chat_id=user_id, 
        text=f"✅ Client Secret Авито успешно сохранен!\n\nДобро пожаловать, {user_name}!"
    )
    menu_m(message)