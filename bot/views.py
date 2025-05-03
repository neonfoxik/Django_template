from traceback import format_exc

from asgiref.sync import sync_to_async
from bot.handlers import *
from django.conf import settings
from django.http import HttpRequest, JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST
from telebot.apihelper import ApiTelegramException
from telebot.types import Update

from bot import bot, logger


@require_GET
def set_webhook(request: HttpRequest) -> JsonResponse:
    """Setting webhook."""
    bot.set_webhook(url=f"{settings.HOOK}/bot/{settings.BOT_TOKEN}")
    bot.send_message(settings.OWNER_ID, "webhook set")
    return JsonResponse({"message": "OK"}, status=200)


@require_GET
def status(request: HttpRequest) -> JsonResponse:
    return JsonResponse({"message": "OK"}, status=200)


@csrf_exempt
@require_POST
@sync_to_async
def index(request: HttpRequest) -> JsonResponse:
    if request.META.get("CONTENT_TYPE") != "application/json":
        return JsonResponse({"message": "Bad Request"}, status=403)

    json_string = request.body.decode("utf-8")
    update = Update.de_json(json_string)
    try:
        bot.process_new_updates([update])
    except ApiTelegramException as e:
        logger.error(f"Telegram exception. {e} {format_exc()}")
    except ConnectionError as e:
        logger.error(f"Connection error. {e} {format_exc()}")
    except Exception as e:
        bot.send_message(settings.OWNER_ID, f'Error from index: {e}')
        logger.error(f"Unhandled exception. {e} {format_exc()}")
    return JsonResponse({"message": "OK"}, status=200)


"""Common"""
admin = bot.message_handler(commands=["admin"])(get_users)
start = bot.message_handler(commands=["start"])(start)

get_user_info = bot.callback_query_handler(lambda c: c.data.startswith("admin_"))(get_user_info)

# Добавляем функцию-посредник для отладки daily_report
def daily_report_wrapper(call):
    logger.info(f"ОТЛАДКА: Обработка daily_report callback: {call.data}")
    logger.info(f"ОТЛАДКА: from_user.id = {call.from_user.id}, chat_id = {call.message.chat.id}")
    try:
        daily_report(call)
    except Exception as e:
        logger.error(f"Ошибка в daily_report_wrapper: {e}")
        logger.exception("Полный стек-трейс ошибки:")
        bot.send_message(call.message.chat.id, f"❌ Произошла ошибка: {str(e)}")

# Добавляем функцию-посредник для отладки weekly_report
def weekly_report_wrapper(call):
    logger.info(f"ОТЛАДКА: Обработка weekly_report callback: {call.data}")
    logger.info(f"ОТЛАДКА: from_user.id = {call.from_user.id}, chat_id = {call.message.chat.id}")
    try:
        weekly_report(call)
    except Exception as e:
        logger.error(f"Ошибка в weekly_report_wrapper: {e}")
        logger.exception("Полный стек-трейс ошибки:")
        bot.send_message(call.message.chat.id, f"❌ Произошла ошибка: {str(e)}")

# Обработчик дневных отчетов из кнопок меню и кнопок выбора аккаунта
daily_report_handler = bot.callback_query_handler(func=lambda c: c.data == "daily_report" or c.data.startswith("daily_report_"))(daily_report_wrapper)

# Обработчик недельных отчетов из кнопок меню и кнопок выбора аккаунта
weekly_report_handler = bot.callback_query_handler(func=lambda c: c.data == "weekly_report" or c.data.startswith("weekly_report_"))(weekly_report_wrapper)

@bot.message_handler(commands=["daily"])
def daily_command(message):
    """Обработчик команды /daily для получения дневного отчета"""
    from bot.handlers.common import get_daily_reports_for_chat
    chat_id = message.chat.id
    logger.info(f"ОТЛАДКА: Команда /daily в чате {chat_id} от пользователя {message.from_user.id}")
    get_daily_reports_for_chat(chat_id)

@bot.message_handler(commands=["weekly"])
def weekly_command(message):
    """Обработчик команды /weekly для получения недельного отчета"""
    from bot.handlers.common import get_weekly_reports_for_chat
    chat_id = message.chat.id
    logger.info(f"ОТЛАДКА: Команда /weekly в чате {chat_id} от пользователя {message.from_user.id}")
    get_weekly_reports_for_chat(chat_id)