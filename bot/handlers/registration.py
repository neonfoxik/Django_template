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
        mesg = bot.send_message(message.chat.id, 'Введите секретный ключ Авито API')
        bot.register_next_step_handler(mesg, get_user_avito_api_key)
        

def get_user_avito_api_key(message):
    from bot.handlers.common import menu_m
    avito_api = message.text
    user_id = message.from_user.id
    user = User.objects.create(
        telegram_id=user_id,
        user_name=message.from_user.first_name,
        avito_api_key = avito_api
    )
    user.save()
    bot.send_message(chat_id=user_id, text="Секретный ключ Авито API успешно сохранен.")
    menu_m(message)