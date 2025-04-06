import datetime
from django.conf import settings
from bot.models import User
from bot.handlers.common import send_daily_report, send_weekly_report


def send_daily_reports_to_all_users():
    """Отправка ежедневных отчетов всем пользователям"""
    users = User.objects.filter(avito_api_key__isnull=False).exclude(avito_api_key="none")
    for user in users:
        try:
            send_daily_report(user.telegram_id)
        except Exception as e:
            print(f"Ошибка при отправке ежедневного отчета пользователю {user.telegram_id}: {e}")


def send_weekly_reports_to_all_users():
    """Отправка еженедельных отчетов всем пользователям"""
    # Проверяем, что сегодня понедельник (день недели = 0)
    if datetime.datetime.now().weekday() == 0:
        users = User.objects.filter(avito_api_key__isnull=False).exclude(avito_api_key="none")
        for user in users:
            try:
                send_weekly_report(user.telegram_id)
            except Exception as e:
                print(f"Ошибка при отправке еженедельного отчета пользователю {user.telegram_id}: {e}")


# Функции для запуска через cron
def daily_task():
    """Задача для ежедневного запуска через cron"""
    send_daily_reports_to_all_users()


def weekly_task():
    """Задача для еженедельного запуска через cron"""
    send_weekly_reports_to_all_users()
