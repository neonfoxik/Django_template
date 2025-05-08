import os
import sys
import logging
import django
import unittest.mock as mock

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dd.settings')
django.setup()

# Настраиваем логирование
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Создаем моки для функций бота
class MockMessage:
    def __init__(self, message_id=1):
        self.message_id = message_id

class MockBot:
    def send_message(self, chat_id, text, **kwargs):
        print(f"\n--- ОТПРАВКА СООБЩЕНИЯ В ЧАТ {chat_id} ---")
        print(text)
        print("----------- КОНЕЦ СООБЩЕНИЯ -----------")
        return MockMessage()
        
    def delete_message(self, chat_id, message_id):
        print(f"[Удаление сообщения {message_id} из чата {chat_id}]")

# Применяем мок к боту
import bot.handlers.common as common
original_bot = common.bot
common.bot = MockBot()

# Импортируем необходимые функции
from bot.handlers.common import (
    get_daily_reports_for_chat,
    get_weekly_reports_for_chat,
    daily_report_for_account,
    weekly_report_for_account
)
from bot.models import AvitoAccount

try:
    # Получаем ID первого аккаунта для тестирования
    account = AvitoAccount.objects.filter(
        client_id__isnull=False, 
        client_secret__isnull=False
    ).exclude(client_id="none").first()
    
    if account:
        account_id = account.id
        print(f"\n=== Тестирование с аккаунтом {account.name} (ID: {account_id}) ===\n")
        
        # Эмулируем выполнение команды /daily для конкретного аккаунта
        print("Эмуляция daily_report_for_account()...")
        daily_report_for_account(chat_id="123456789", account_id=account_id)
        
        # Эмуляция команды /weekly для конкретного аккаунта
        print("\nЭмуляция weekly_report_for_account()...")
        weekly_report_for_account(chat_id="123456789", account_id=account_id)
        
        # Дополнительно: если у аккаунта настроено поле daily_report_tg_id
        if account.daily_report_tg_id:
            print(f"\nЭмуляция get_daily_reports_for_chat() для TG ID: {account.daily_report_tg_id}...")
            get_daily_reports_for_chat(account.daily_report_tg_id)
        else:
            print(f"\nПропускаем get_daily_reports_for_chat() - daily_report_tg_id не настроен.")
        
        # Дополнительно: если у аккаунта настроено поле weekly_report_tg_id
        if account.weekly_report_tg_id:
            print(f"\nЭмуляция get_weekly_reports_for_chat() для TG ID: {account.weekly_report_tg_id}...")
            get_weekly_reports_for_chat(account.weekly_report_tg_id)
        else:
            print(f"\nПропускаем get_weekly_reports_for_chat() - weekly_report_tg_id не настроен.")
    else:
        print("Не найдено ни одного аккаунта с настроенными client_id и client_secret!")
        
except Exception as e:
    logger.error(f"Ошибка при выполнении теста: {e}")
    print(f"Произошла ошибка: {e}")
finally:
    # Восстанавливаем оригинальный объект бота
    common.bot = original_bot 