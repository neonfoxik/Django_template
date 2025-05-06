import logging
import datetime
from django.conf import settings
from django.utils import timezone
from bot.models import AvitoAccount, AvitoAccountDailyStats
from bot import bot

logger = logging.getLogger(__name__)

def check_anomalies():
    """
    Проверяет аномалии в статистике аккаунтов и отправляет уведомления
    """
    try:
        logger.info("Запуск проверки аномалий в статистике аккаунтов")
        
        # Получаем текущую дату
        today = timezone.now().date()
        yesterday = today - datetime.timedelta(days=1)
        
        # Получаем все активные аккаунты
        accounts = AvitoAccount.objects.filter(
            client_id__isnull=False, 
            client_secret__isnull=False
        ).exclude(client_id="none")
        
        logger.info(f"Проверка аномалий для {accounts.count()} аккаунтов")
        
        for account in accounts:
            try:
                # Получаем статистику за вчера и позавчера
                yesterday_stats = AvitoAccountDailyStats.objects.filter(
                    avito_account=account,
                    date=yesterday
                ).first()
                
                day_before_yesterday = yesterday - datetime.timedelta(days=1)
                day_before_stats = AvitoAccountDailyStats.objects.filter(
                    avito_account=account,
                    date=day_before_yesterday
                ).first()
                
                if not yesterday_stats or not day_before_stats:
                    logger.info(f"Недостаточно данных для аккаунта {account.name}")
                    continue
                
                # Проверяем аномалии
                anomalies = detect_anomalies(account, yesterday_stats, day_before_stats)
                
                if anomalies:
                    # Отправляем уведомление, если есть аномалии
                    send_anomaly_notification(account, anomalies, yesterday)
                    
            except Exception as e:
                logger.error(f"Ошибка при проверке аномалий для аккаунта {account.name}: {e}")
        
        logger.info("Проверка аномалий завершена")
        
    except Exception as e:
        logger.error(f"Ошибка при проверке аномалий: {e}")

def detect_anomalies(account, yesterday_stats, day_before_stats):
    """
    Выявляет аномалии путем сравнения вчерашней статистики с позавчерашней
    
    Args:
        account: Экземпляр модели AvitoAccount
        yesterday_stats: Статистика за вчера
        day_before_stats: Статистика за позавчера
        
    Returns:
        list: Список обнаруженных аномалий
    """
    anomalies = []
    
    # Пороговые значения для обнаружения аномалий (в процентах)
    THRESHOLD_CALLS = 50  # Изменение звонков на 50%
    THRESHOLD_VIEWS = 40  # Изменение просмотров на 40%
    THRESHOLD_CONTACTS = 40  # Изменение контактов на 40%
    THRESHOLD_EXPENSE = 100  # Увеличение расходов на 100% (в 2 раза)
    
    # Минимальные абсолютные значения для учета аномалий
    MIN_CALLS = 5
    MIN_VIEWS = 50
    MIN_CONTACTS = 10
    MIN_EXPENSE = 100
    
    # Расчет процентных изменений
    # Звонки
    if day_before_stats.total_calls >= MIN_CALLS:
        if yesterday_stats.total_calls == 0 and day_before_stats.total_calls > 0:
            # Полное исчезновение звонков
            anomalies.append({
                "type": "calls_drop",
                "previous": day_before_stats.total_calls,
                "current": 0,
                "change_percent": -100,
                "message": f"Полное отсутствие звонков (было {day_before_stats.total_calls})"
            })
        elif yesterday_stats.total_calls > 0 and day_before_stats.total_calls > 0:
            percent_change = ((yesterday_stats.total_calls - day_before_stats.total_calls) / day_before_stats.total_calls) * 100
            if abs(percent_change) >= THRESHOLD_CALLS:
                direction = "увеличение" if percent_change > 0 else "снижение"
                anomalies.append({
                    "type": "calls_change",
                    "previous": day_before_stats.total_calls,
                    "current": yesterday_stats.total_calls,
                    "change_percent": percent_change,
                    "message": f"Резкое {direction} звонков на {abs(percent_change):.1f}% ({day_before_stats.total_calls} → {yesterday_stats.total_calls})"
                })
    
    # Просмотры
    if day_before_stats.views >= MIN_VIEWS:
        if yesterday_stats.views == 0 and day_before_stats.views > 0:
            # Полное исчезновение просмотров
            anomalies.append({
                "type": "views_drop",
                "previous": day_before_stats.views,
                "current": 0,
                "change_percent": -100,
                "message": f"Полное отсутствие просмотров (было {day_before_stats.views})"
            })
        elif yesterday_stats.views > 0 and day_before_stats.views > 0:
            percent_change = ((yesterday_stats.views - day_before_stats.views) / day_before_stats.views) * 100
            if abs(percent_change) >= THRESHOLD_VIEWS:
                direction = "увеличение" if percent_change > 0 else "снижение"
                anomalies.append({
                    "type": "views_change",
                    "previous": day_before_stats.views,
                    "current": yesterday_stats.views,
                    "change_percent": percent_change,
                    "message": f"Резкое {direction} просмотров на {abs(percent_change):.1f}% ({day_before_stats.views} → {yesterday_stats.views})"
                })
    
    # Контакты
    if day_before_stats.contacts >= MIN_CONTACTS:
        if yesterday_stats.contacts == 0 and day_before_stats.contacts > 0:
            # Полное исчезновение контактов
            anomalies.append({
                "type": "contacts_drop",
                "previous": day_before_stats.contacts,
                "current": 0,
                "change_percent": -100,
                "message": f"Полное отсутствие контактов (было {day_before_stats.contacts})"
            })
        elif yesterday_stats.contacts > 0 and day_before_stats.contacts > 0:
            percent_change = ((yesterday_stats.contacts - day_before_stats.contacts) / day_before_stats.contacts) * 100
            if abs(percent_change) >= THRESHOLD_CONTACTS:
                direction = "увеличение" if percent_change > 0 else "снижение"
                anomalies.append({
                    "type": "contacts_change",
                    "previous": day_before_stats.contacts,
                    "current": yesterday_stats.contacts,
                    "change_percent": percent_change,
                    "message": f"Резкое {direction} контактов на {abs(percent_change):.1f}% ({day_before_stats.contacts} → {yesterday_stats.contacts})"
                })
    
    # Расходы
    if day_before_stats.daily_expense >= MIN_EXPENSE:
        if yesterday_stats.daily_expense > day_before_stats.daily_expense:
            percent_change = ((yesterday_stats.daily_expense - day_before_stats.daily_expense) / day_before_stats.daily_expense) * 100
            if percent_change >= THRESHOLD_EXPENSE:
                anomalies.append({
                    "type": "expense_increase",
                    "previous": day_before_stats.daily_expense,
                    "current": yesterday_stats.daily_expense,
                    "change_percent": percent_change,
                    "message": f"Резкое увеличение расходов на {percent_change:.1f}% ({day_before_stats.daily_expense:.2f} ₽ → {yesterday_stats.daily_expense:.2f} ₽)"
                })
    
    # Проверяем коэффициент конверсии (отношение контактов к просмотрам)
    if (day_before_stats.views >= MIN_VIEWS and yesterday_stats.views >= MIN_VIEWS and
        day_before_stats.contacts > 0 and yesterday_stats.contacts > 0):
        
        prev_conversion = (day_before_stats.contacts / day_before_stats.views) * 100
        curr_conversion = (yesterday_stats.contacts / yesterday_stats.views) * 100
        
        if prev_conversion > 0:
            percent_change = ((curr_conversion - prev_conversion) / prev_conversion) * 100
            if abs(percent_change) >= THRESHOLD_CONTACTS:
                direction = "увеличение" if percent_change > 0 else "снижение"
                anomalies.append({
                    "type": "conversion_change",
                    "previous": prev_conversion,
                    "current": curr_conversion,
                    "change_percent": percent_change,
                    "message": f"Резкое {direction} конверсии на {abs(percent_change):.1f}% ({prev_conversion:.2f}% → {curr_conversion:.2f}%)"
                })
    
    return anomalies

def send_anomaly_notification(account, anomalies, date):
    """
    Отправляет уведомление о выявленных аномалиях
    
    Args:
        account: Экземпляр модели AvitoAccount
        anomalies: Список аномалий
        date: Дата, за которую обнаружены аномалии
    """
    try:
        # Проверяем, куда отправлять уведомления
        if not account.daily_report_tg_id:
            logger.warning(f"Для аккаунта {account.name} не указан получатель уведомлений")
            return
            
        # Формируем сообщение с уведомлением
        message_text = f"⚠️ *УВЕДОМЛЕНИЕ ОБ АНОМАЛИЯХ* ⚠️\n\n"
        message_text += f"*Аккаунт:* {account.name}\n"
        message_text += f"*Дата:* {date}\n\n"
        message_text += f"*Обнаружены следующие аномалии:*\n"
        
        # Сортируем аномалии по серьезности (абсолютному значению процентного изменения)
        sorted_anomalies = sorted(anomalies, key=lambda x: abs(x.get('change_percent', 0)), reverse=True)
        
        for anomaly in sorted_anomalies:
            emoji = "🔴" if anomaly.get('change_percent', 0) < 0 else "🟢"
            message_text += f"{emoji} {anomaly.get('message')}\n"
        
        # Отправляем сообщение
        bot.send_message(
            chat_id=account.daily_report_tg_id,
            text=message_text,
            parse_mode="Markdown"
        )
        
        logger.info(f"Отправлено уведомление об аномалиях для аккаунта {account.name}")
        
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомления об аномалиях для аккаунта {account.name}: {e}")


if __name__ == "__main__":
    # Можно запустить скрипт непосредственно для тестирования
    check_anomalies() 