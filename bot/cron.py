import datetime
import logging
from django.conf import settings
from bot.models import User, AvitoAccount
from bot.handlers.common import send_daily_report, send_weekly_report
from bot.services import get_access_token, get_user_balance_info

logger = logging.getLogger(__name__)


def send_daily_reports_to_all_users():
    """Отправка ежедневных отчетов всем пользователям"""
    accounts = AvitoAccount.objects.filter(
        client_id__isnull=False, 
        client_secret__isnull=False
    ).exclude(client_id="none")
    
    logger.info(f'Найдено аккаунтов для ежедневных отчетов: {accounts.count()}')
    
    for account in accounts:
        try:
            # Отправляем дневной отчет в указанный telegram_id
            if account.daily_report_tg_id:
                logger.info(f"Отправка ежедневного отчета для аккаунта {account.name} на ID: {account.daily_report_tg_id}")
                send_daily_report(account.daily_report_tg_id, account.id)
            else:
                logger.info(f"Аккаунт {account.name} не имеет указанного получателя ежедневных отчетов")
        except Exception as e:
            logger.error(f"Ошибка при отправке ежедневного отчета для аккаунта {account.name}: {e}")


def send_weekly_reports_to_all_users():
    """Отправка еженедельных отчетов всем пользователям"""
    accounts = AvitoAccount.objects.filter(
        client_id__isnull=False, 
        client_secret__isnull=False
    ).exclude(client_id="none")
    
    logger.info(f'Найдено аккаунтов для еженедельных отчетов: {accounts.count()}')
    
    for account in accounts:
        try:
            # Отправляем недельный отчет
            if account.weekly_report_tg_id:
                logger.info(f"Отправка еженедельного отчета для аккаунта {account.name} на ID: {account.weekly_report_tg_id}")
                send_weekly_report(account.weekly_report_tg_id, account.id)
            else:
                logger.info(f"Аккаунт {account.name} не имеет указанного получателя еженедельных отчетов")
        except Exception as e:
            logger.error(f"Ошибка при отправке еженедельного отчета для аккаунта {account.name}: {e}")


def track_user_expenses():
    """Отслеживание расходов аккаунтов на основе изменения баланса"""
    accounts = AvitoAccount.objects.filter(
        client_id__isnull=False, 
        client_secret__isnull=False
    ).exclude(client_id="none")
    
    current_time = datetime.datetime.now()
    
    for account in accounts:
        try:
            # Получаем токен доступа
            access_token = get_access_token(account.client_id, account.client_secret)
            if not access_token:
                logger.error(f"Не удалось получить токен доступа для аккаунта {account.name}")
                continue
                
            # Получаем текущий баланс аккаунта
            balance_info = get_user_balance_info(access_token)
            
            # Используем сумму реального баланса, бонусов и авансовых платежей
            current_balance = balance_info["balance_real"] + balance_info["balance_bonus"] + balance_info["advance"]
            
            # Если это первая проверка баланса
            if account.last_balance_check is None:
                account.last_balance = current_balance
                account.last_balance_check = current_time
                account.save()
                logger.info(f"Инициализация баланса аккаунта {account.name}: {current_balance}")
                continue
            
            # Проверяем, уменьшился ли баланс (произошел расход)
            if current_balance < account.last_balance:
                # Рассчитываем сумму расхода
                expense_amount = account.last_balance - current_balance
                
                # Обновляем дневной расход
                account.daily_expense += expense_amount
                
                # Обновляем недельный расход
                account.weekly_expense += expense_amount
                
                logger.info(f"Зафиксирован расход для аккаунта {account.name}: {expense_amount} р. "
                           f"Дневной расход: {account.daily_expense} р., Недельный расход: {account.weekly_expense} р.")
            
            # Обновляем значение последнего баланса и времени проверки
            account.last_balance = current_balance
            account.last_balance_check = current_time
            account.save()
            
        except Exception as e:
            logger.error(f"Ошибка при отслеживании расходов аккаунта {account.name}: {e}")


def reset_daily_expenses():
    """Сброс дневных расходов в начале нового дня"""
    try:
        # Сбрасываем дневной расход для всех аккаунтов
        accounts = AvitoAccount.objects.all()
        for account in accounts:
            if account.daily_expense > 0:
                logger.info(f"Сброс дневного расхода для аккаунта {account.name}: {account.daily_expense} р.")
                account.daily_expense = 0
                account.save()
    except Exception as e:
        logger.error(f"Ошибка при сбросе дневных расходов: {e}")


def reset_weekly_expenses():
    """Сброс недельных расходов в начале новой недели"""
    try:
        # Сбрасываем недельный расход для всех аккаунтов
        accounts = AvitoAccount.objects.all()
        for account in accounts:
            if account.weekly_expense > 0:
                logger.info(f"Сброс недельного расхода для аккаунта {account.name}: {account.weekly_expense} р.")
                account.weekly_expense = 0
                account.save()
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

