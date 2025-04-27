import datetime
import logging
from django.conf import settings
from bot.models import User
from bot.handlers.common import send_daily_report, send_weekly_report
from bot.services import get_access_token, get_user_balance_info

logger = logging.getLogger(__name__)


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


def track_user_expenses():
    """Отслеживание расходов пользователей на основе изменения баланса"""
    users = User.objects.filter(client_id__isnull=False, client_secret__isnull=False).exclude(client_id="none")
    current_time = datetime.datetime.now()
    
    for user in users:
        try:
            # Получаем токен доступа
            access_token = get_access_token(user.client_id, user.client_secret)
            if not access_token:
                logger.error(f"Не удалось получить токен доступа для пользователя {user.telegram_id}")
                continue
                
            # Получаем текущий баланс пользователя
            balance_info = get_user_balance_info(access_token)
            
            # Используем сумму реального баланса, бонусов и авансовых платежей
            current_balance = balance_info["balance_real"] + balance_info["balance_bonus"] + balance_info["advance"]
            
            # Если это первая проверка баланса
            if user.last_balance_check is None:
                user.last_balance = current_balance
                user.last_balance_check = current_time
                user.save()
                logger.info(f"Инициализация баланса пользователя {user.telegram_id}: {current_balance}")
                continue
            
            # Проверяем, уменьшился ли баланс (произошел расход)
            if current_balance < user.last_balance:
                # Рассчитываем сумму расхода
                expense_amount = user.last_balance - current_balance
                
                # Обновляем дневной расход
                user.daily_expense += expense_amount
                
                # Обновляем недельный расход
                user.weekly_expense += expense_amount
                
                logger.info(f"Зафиксирован расход для пользователя {user.telegram_id}: {expense_amount} р. "
                           f"Дневной расход: {user.daily_expense} р., Недельный расход: {user.weekly_expense} р.")
            
            # Обновляем значение последнего баланса и времени проверки
            user.last_balance = current_balance
            user.last_balance_check = current_time
            user.save()
            
        except Exception as e:
            logger.error(f"Ошибка при отслеживании расходов пользователя {user.telegram_id}: {e}")


def reset_daily_expenses():
    """Сброс дневных расходов в начале нового дня"""
    try:
        # Сбрасываем дневной расход для всех пользователей
        users = User.objects.all()
        for user in users:
            if user.daily_expense > 0:
                logger.info(f"Сброс дневного расхода для пользователя {user.telegram_id}: {user.daily_expense} р.")
                user.daily_expense = 0
                user.save()
    except Exception as e:
        logger.error(f"Ошибка при сбросе дневных расходов: {e}")


def reset_weekly_expenses():
    """Сброс недельных расходов в начале новой недели"""
    try:
        # Сбрасываем недельный расход для всех пользователей
        users = User.objects.all()
        for user in users:
            if user.weekly_expense > 0:
                logger.info(f"Сброс недельного расхода для пользователя {user.telegram_id}: {user.weekly_expense} р.")
                user.weekly_expense = 0
                user.save()
    except Exception as e:
        logger.error(f"Ошибка при сбросе недельных расходов: {e}")


# Функции для запуска через cron
def daily_task():
    """Задача для ежедневного запуска через cron"""
    send_daily_reports_to_all_users()
    reset_daily_expenses()


def weekly_task():
    """Задача для еженедельного запуска через cron"""
    send_weekly_reports_to_all_users()
    reset_weekly_expenses()


def minutely_task():
    """Задача для запуска каждую минуту через cron"""
    track_user_expenses()

