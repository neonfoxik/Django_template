import logging
from django.core.management.base import BaseCommand
from bot.models import AvitoAccount
from bot.handlers.common import send_weekly_report

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Отправляет еженедельные отчеты всем пользователям и сбрасывает недельные расходы'

    def handle(self, *args, **kwargs):
        self.stdout.write('Запуск отправки еженедельных отчетов...')
        self.send_weekly_reports_to_all_users()
        self.reset_weekly_expenses()
        self.stdout.write(self.style.SUCCESS('Еженедельные отчеты успешно отправлены'))

    def send_weekly_reports_to_all_users(self):
        """Отправка еженедельных отчетов всем пользователям"""
        accounts = AvitoAccount.objects.filter(
            client_id__isnull=False, 
            client_secret__isnull=False
        ).exclude(client_id="none")
        
        self.stdout.write(f'Найдено аккаунтов для отправки отчетов: {accounts.count()}')
        
        for account in accounts:
            try:
                # Отправляем недельный отчет
                if account.weekly_report_tg_id:
                    self.stdout.write(f"Отправка отчета для аккаунта {account.name} на ID: {account.weekly_report_tg_id}")
                    send_weekly_report(account.weekly_report_tg_id, account.id)
                else:
                    self.stdout.write(f"Аккаунт {account.name} не имеет указанного получателя еженедельных отчетов")
            except Exception as e:
                logger.error(f"Ошибка при отправке еженедельного отчета для аккаунта {account.name}: {e}")

    def reset_weekly_expenses(self):
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
