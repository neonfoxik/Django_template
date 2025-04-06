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

start = bot.message_handler(commands=["start"])(start)
admin = bot.message_handler(commands=["admin"])(admin_menu)
newsletter = bot.callback_query_handler(lambda c: c.data == "newsletter")(newsletter)
events_menu = bot.callback_query_handler(lambda c: c.data == "events_menu")(events_menu)
FAQ = bot.callback_query_handler(lambda c: c.data == "FAQ")(FAQ)
main_video_menu = bot.callback_query_handler(lambda c: c.data == "main_video_menu")(menu_video)
check_subscription = bot.callback_query_handler(lambda c: c.data == "check_subscription")(start_registration_call)
menu_call = bot.callback_query_handler(lambda c: c.data == "main_menu")(menu_call)
coins_menu = bot.callback_query_handler(lambda c: c.data == "coins_menu")(coins_menu)
'coins_farm = bot.callback_query_handler(lambda c: c.data == "coins_farm")(coins_farm)'
coins_trade = bot.callback_query_handler(lambda c: c.data == "coins_trade")(coins_trade)
profile = bot.callback_query_handler(lambda c: c.data == "profile")(profile)
referal_menu = bot.callback_query_handler(lambda c: c.data == "referal_menu")(referal_menu)
get_ref_link = bot.callback_query_handler(lambda c: c.data == "get_referal_link")(get_ref_link)
event_check = bot.callback_query_handler(lambda c: c.data.startswith("event_check_"))(event_check)
send_goods_to_admin = bot.callback_query_handler(lambda c: c.data.startswith("goods_"))(send_goods_to_admin)
