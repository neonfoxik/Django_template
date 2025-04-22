import datetime
import logging
from django.conf import settings
from bot.models import User
from bot.handlers.common import send_daily_report, send_weekly_report
from bot.services import update_user_chats_count, get_access_token

logger = logging.getLogger(__name__)


def update_users_chats():
    """Обновление чатов пользователей"""
    users = User.objects.filter(client_id__isnull=False, client_secret__isnull=False).exclude(client_id="none")
    for user in users:
        try:
            access_token = get_access_token(user.client_id, user.client_secret)
            if not access_token:
                continue
                
            # Обновляем счетчики чатов
            new_chats = update_user_chats_count(user, access_token)
            if new_chats > 0:
                logger.info(f"У пользователя {user.telegram_id} появилось {new_chats} новых чатов")
            
            user.save()
            
        except Exception as e:
            logger.error(f"Ошибка при обновлении данных пользователя {user.telegram_id}: {e}")


def send_daily_reports_to_all_users():
    """Отправка ежедневных отчетов всем пользователям"""
    users = User.objects.filter(client_id__isnull=False, client_secret__isnull=False).exclude(client_id="none")
    for user in users:
        try:
            # Отправляем дневной отчет
            send_daily_report(user.telegram_id)
        except Exception as e:
            logger.error(f"Ошибка при отправке ежедневного отчета пользователю {user.telegram_id}: {e}")


def send_weekly_reports_to_all_users():
    """Отправка еженедельных отчетов всем пользователям"""
    users = User.objects.filter(client_id__isnull=False, client_secret__isnull=False).exclude(client_id="none")
    for user in users:
        try:
            # Отправляем недельный отчет
            send_weekly_report(user.telegram_id)
        except Exception as e:
            logger.error(f"Ошибка при отправке еженедельного отчета пользователю {user.telegram_id}: {e}")


# Функции для запуска через cron
def daily_task():
    """Задача для ежедневного запуска через cron"""
    send_daily_reports_to_all_users()


def weekly_task():
    """Задача для еженедельного запуска через cron"""
    send_weekly_reports_to_all_users()


def chat_monitor_task():
    """Задача для мониторинга чатов пользователей через cron"""
    update_users_chats()
