import os
import sys
import django
import logging

# Настройка Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'dd.settings')
django.setup()

# Настройка логгера
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Импортируем необходимые функции и модели
from bot.models import User, AvitoAccount, UserAvitoAccount

def process_user_info():
    """Тестирование получения информации о пользователях из администраторского интерфейса"""
    
    # Получаем всех пользователей
    users = User.objects.all()
    logger.info(f"Найдено пользователей: {users.count()}")
    
    if not users:
        logger.warning("Пользователи не найдены. Добавьте пользователей в систему.")
        return
    
    # Получаем список аккаунтов
    accounts = AvitoAccount.objects.all()
    logger.info(f"Найдено аккаунтов: {accounts.count()}")
    
    if not accounts:
        logger.warning("Аккаунты не найдены. Добавьте аккаунты в систему.")
        return
    
    # Выводим информацию о каждом пользователе и привязанных аккаунтах
    for user in users:
        logger.info(f"Пользователь: {user.user_name} (ID: {user.telegram_id})")
        
        # Получаем связанные аккаунты через промежуточную модель
        user_account_links = UserAvitoAccount.objects.filter(user=user)
        
        if user_account_links:
            logger.info(f"Связанные аккаунты:")
            for link in user_account_links:
                account = link.avito_account
                logger.info(f"- {account.name} (ID: {account.id})")
                
                # Выводим API ключи
                if account.client_id and account.client_secret and account.client_id != "none":
                    logger.info(f"  - API ключ настроен")
                else:
                    logger.info(f"  - API ключ не настроен")
                
                # Проверяем настройки отчетов
                if account.daily_report_tg_id:
                    logger.info(f"  - Настроена отправка дневных отчетов на ID: {account.daily_report_tg_id}")
                else:
                    logger.info(f"  - Отправка дневных отчетов не настроена")
                
                if account.weekly_report_tg_id:
                    logger.info(f"  - Настроена отправка недельных отчетов на ID: {account.weekly_report_tg_id}")
                else:
                    logger.info(f"  - Отправка недельных отчетов не настроена")
        else:
            logger.info("Нет связанных аккаунтов")

if __name__ == "__main__":
    print("\n=== Тестирование административных функций ===")
    process_user_info() 