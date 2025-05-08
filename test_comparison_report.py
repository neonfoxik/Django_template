import os
import sys
import django
import datetime

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dd.settings')
django.setup()

# Импортируем необходимые функции и модели
from bot.handlers.common import format_report_message_with_comparison, send_daily_report, send_weekly_report
from bot.models import AvitoAccount
from bot.statistics import get_daily_statistics
import logging

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def process_real_reports():
    # Получаем все активные аккаунты
    accounts = AvitoAccount.objects.filter(
        client_id__isnull=False, 
        client_secret__isnull=False
    ).exclude(client_id="none")
    
    logger.info(f'Найдено аккаунтов для обработки: {accounts.count()}')
    
    for account in accounts:
        try:
            # Если указан Telegram ID для дневных отчетов
            if account.daily_report_tg_id:
                logger.info(f"Обработка дневного отчета для аккаунта {account.name}")
                send_daily_report(account.daily_report_tg_id, account.id)
            else:
                logger.info(f"Аккаунт {account.name} не имеет указанного получателя дневных отчетов")
            
            # Если указан Telegram ID для недельных отчетов
            if account.weekly_report_tg_id:
                logger.info(f"Обработка недельного отчета для аккаунта {account.name}")
                send_weekly_report(account.weekly_report_tg_id, account.id)
            else:
                logger.info(f"Аккаунт {account.name} не имеет указанного получателя недельных отчетов")
        except Exception as e:
            logger.error(f"Ошибка при обработке отчетов для аккаунта {account.name}: {e}")

if __name__ == "__main__":
    process_real_reports() 