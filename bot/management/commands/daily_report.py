import logging
from django.core.management.base import BaseCommand
from bot.models import AvitoAccount
from bot.handlers.common import send_daily_report

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Отправляет ежедневные отчеты всем пользователям и сбрасывает дневные расходы'

    def handle(self, *args, **kwargs):
        self.stdout.write('Запуск отправки ежедневных отчетов...')
        self.send_daily_reports_to_all_users()
        self.reset_daily_expenses()
        self.stdout.write(self.style.SUCCESS('Ежедневные отчеты успешно отправлены'))

    def send_daily_reports_to_all_users(self):
        """Отправка ежедневных отчетов всем пользователям"""
        accounts = AvitoAccount.objects.filter(
            client_id__isnull=False, 
            client_secret__isnull=False, 
            daily_report_tg_id__isnull=False
        ).exclude(client_id="none")
        
        for account in accounts:
            try:
                # Отправляем дневной отчет в указанный telegram_id
                if account.daily_report_tg_id:
                    # Передаем telegram_id и account_id
                    self.stdout.write(f"Отправка отчета для аккаунта {account.name} на ID: {account.daily_report_tg_id}")
                    send_daily_report(account.daily_report_tg_id, account.id)
            except Exception as e:
                logger.error(f"Ошибка при отправке ежедневного отчета для аккаунта {account.name}: {e}")

    def reset_daily_expenses(self):
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
