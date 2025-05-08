import os
import sys
import django
import logging
import datetime

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dd.settings')
django.setup()

# Импортируем функцию форматирования и API-интерфейс
from bot.handlers.common import format_report_message, save_daily_report_to_db, save_weekly_report_to_db
from bot.models import AvitoAccount
from bot.statistics import get_daily_statistics, get_weekly_statistics

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def format_real_reports():
    # Получаем все активные аккаунты
    accounts = AvitoAccount.objects.filter(
        client_id__isnull=False, 
        client_secret__isnull=False
    ).exclude(client_id="none")
    
    logger.info(f'Найдено аккаунтов для обработки: {accounts.count()}')
    
    for account in accounts:
        try:
            # Получаем реальные данные для дневного отчета
            logger.info(f"Получение данных для дневного отчета аккаунта {account.name}")
            daily_data = get_daily_statistics(account.client_id, account.client_secret)
            
            if daily_data:
                # Сохраняем дневной отчет в базу данных
                logger.info(f"Сохранение дневного отчета в базу данных для аккаунта {account.name} за {daily_data.get('date')}")
                daily_report_db = save_daily_report_to_db(daily_data, account)
                logger.info(f"Результат сохранения дневного отчета: {daily_report_db}")
                
                # Форматируем отчет для отображения
                daily_report = format_report_message(daily_data, account.name, is_weekly=False)
                print(f"\n=== ДНЕВНОЙ ОТЧЕТ ДЛЯ {account.name} ===")
                print(daily_report)
            else:
                logger.warning(f"Не удалось получить данные для дневного отчета аккаунта {account.name}")
            
            # Получаем реальные данные для недельного отчета
            logger.info(f"Получение данных для недельного отчета аккаунта {account.name}")
            weekly_data = get_weekly_statistics(account.client_id, account.client_secret)
            
            if weekly_data:
                # Добавляем информацию о периоде
                end_date = datetime.date.today()
                start_date = end_date - datetime.timedelta(days=7)
                weekly_data['period'] = f"{start_date.strftime('%d.%m.%Y')} - {end_date.strftime('%d.%m.%Y')}"
                
                # Сохраняем недельный отчет в базу данных
                logger.info(f"Сохранение недельного отчета в базу данных для аккаунта {account.name} за период {weekly_data.get('period')}")
                weekly_report_db = save_weekly_report_to_db(weekly_data, account)
                logger.info(f"Результат сохранения недельного отчета: {weekly_report_db}")
                
                # Форматируем отчет для отображения
                weekly_report = format_report_message(weekly_data, account.name, is_weekly=True)
                print(f"\n=== НЕДЕЛЬНЫЙ ОТЧЕТ ДЛЯ {account.name} ===")
                print(weekly_report)
            else:
                logger.warning(f"Не удалось получить данные для недельного отчета аккаунта {account.name}")
                
        except Exception as e:
            logger.error(f"Ошибка при обработке отчетов для аккаунта {account.name}: {e}")
            import traceback
            logger.error(traceback.format_exc())

if __name__ == "__main__":
    format_real_reports() 