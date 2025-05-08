import datetime
import logging
from bot.services import (
    get_access_token, 
    get_user_info, 
    get_user_calls, 
    get_missed_calls, 
    get_user_balance_info, 
    get_user_rating_info, 
    get_user_reviews,
    get_chats_by_time,
    get_all_numbers,
    get_avito_user_id,
    get_user_items_stats,
    get_item_promotion_info,
    get_items_statistics,
    get_profile_statistics,
    get_daily_expenses,
    get_weekly_expenses
)

logger = logging.getLogger(__name__)

def get_daily_statistics(client_id, client_secret):
    """
    Получает ежедневную статистику для аккаунта Авито.
    
    Args:
        client_id: ID клиента Авито API
        client_secret: Секретный ключ клиента Авито API
        
    Returns:
        dict: Словарь с данными статистики
    """
    try:
        # Получаем вчерашнюю дату вместо текущей
        current_datetime = datetime.datetime.now()
        yesterday_datetime = current_datetime - datetime.timedelta(days=1)
        yesterday_date = yesterday_datetime.strftime("%d.%m.%Y")
        
        # Начало вчерашнего дня для запросов статистики
        day_start = yesterday_datetime.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
        day_end = yesterday_datetime.replace(hour=23, minute=59, second=59, microsecond=999999).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Получаем токен доступа
        access_token = get_access_token(client_id, client_secret)
        
        if not access_token:
            logger.error("Не удалось получить токен доступа")
            return {
                "date": yesterday_date,
                "calls": {"total": 0, "answered": 0, "missed": 0},
                "chats": {"total": 0, "new": 0},
                "phones_received": 0,
                "rating": 0,
                "reviews": {"total": 0, "today": 0},
                "items": {"total": 0, "with_xl_promotion": 0},
                "statistics": {"views": 0, "contacts": 0, "favorites": 0},
                "balance_real": 0,
                "balance_bonus": 0,
                "advance": 0,
                "expenses": {"total": 0, "details": {}}
            }
            
        # Получаем ID пользователя
        user_id = get_avito_user_id(client_id, client_secret)
        
        if not user_id:
            logger.error("Не удалось получить ID пользователя")
            return {
                "date": yesterday_date,
                "calls": {"total": 0, "answered": 0, "missed": 0},
                "chats": {"total": 0, "new": 0},
                "phones_received": 0,
                "rating": 0,
                "reviews": {"total": 0, "today": 0},
                "items": {"total": 0, "with_xl_promotion": 0},
                "statistics": {"views": 0, "contacts": 0, "favorites": 0},
                "balance_real": 0,
                "balance_bonus": 0,
                "advance": 0,
                "expenses": {"total": 0, "details": {}}
            }
        
        # Получаем звонки за вчерашний день
        calls_data = get_user_calls(access_token, day_start, day_end)
        total_calls = len(calls_data.get('calls', []))
        missed_calls = get_missed_calls(access_token, day_start, day_end)
        answered_calls = total_calls - missed_calls
        
        # Получаем новые чаты за вчерашний день
        new_chats = get_chats_by_time(access_token, day_start, day_end)
        
        # Получаем историю показов телефона
        phones_received = get_all_numbers(access_token, day_start, day_end)
        
        # Получаем рейтинг пользователя
        rating = get_user_rating_info(access_token)
        
        # Получаем отзывы
        reviews_data = get_user_reviews(access_token, day_start, day_end)
        total_reviews = reviews_data.get('total_reviews', 0)
        today_reviews = reviews_data.get('period_reviews', 0)
        
        # Получаем данные о объявлениях
        item_ids = get_user_items_stats(access_token, user_id)
        promotion_info = get_item_promotion_info(access_token, user_id, item_ids)
        
        # Получаем статистику объявлений
        items_stats = get_items_statistics(access_token, user_id, item_ids, day_start, day_end)
        
        # Получаем информацию о балансе
        balance_info = get_user_balance_info(access_token, user_id)
        
        # Получаем данные о расходах за вчерашний день
        expenses = get_daily_expenses(access_token, yesterday_datetime)
        
        # Формируем результат
        result = {
            "date": yesterday_date,
            "calls": {
                "total": total_calls,
                "answered": answered_calls,
                "missed": missed_calls
            },
            "chats": {
                "total": new_chats,
                "new": new_chats  # для совместимости
            },
            "phones_received": phones_received,
            "rating": rating,
            "reviews": {
                "total": total_reviews,
                "today": today_reviews
            },
            "items": {
                "total": promotion_info.get('total_items', 0),
                "with_xl_promotion": promotion_info.get('xl_promotion_count', 0)
            },
            "statistics": {
                "views": items_stats.get('total_views', 0),
                "contacts": items_stats.get('total_contacts', 0),
                "favorites": items_stats.get('total_favorites', 0)
            },
            "balance_real": balance_info.get('balance_real', 0),
            "balance_bonus": balance_info.get('balance_bonus', 0),
            "advance": balance_info.get('advance', 0),
            "expenses": expenses
        }
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении дневной статистики: {e}")
        yesterday_date = (datetime.datetime.now() - datetime.timedelta(days=1)).strftime("%d.%m.%Y")
        return {
            "date": yesterday_date,
            "calls": {"total": 0, "answered": 0, "missed": 0},
            "chats": {"total": 0, "new": 0},
            "phones_received": 0,
            "rating": 0,
            "reviews": {"total": 0, "today": 0},
            "items": {"total": 0, "with_xl_promotion": 0},
            "statistics": {"views": 0, "contacts": 0, "favorites": 0},
            "balance_real": 0,
            "balance_bonus": 0,
            "advance": 0,
            "expenses": {"total": 0, "details": {}}
        }

def get_weekly_statistics(client_id, client_secret):
    """
    Получает еженедельную статистику для аккаунта Авито.
    
    Args:
        client_id: ID клиента Авито API
        client_secret: Секретный ключ клиента Авито API
        
    Returns:
        dict: Словарь с данными статистики
    """
    try:
        # Получаем текущую дату и дату начала недели (7 дней назад)
        current_datetime = datetime.datetime.now()
        current_date = current_datetime.strftime("%d.%m.%Y")
        week_ago_datetime = current_datetime - datetime.timedelta(days=7)
        week_ago_date = week_ago_datetime.strftime("%d.%m.%Y")
        period = f"{week_ago_date} - {current_date}"
        
        # Начало недели для запросов статистики (7 дней назад)
        week_start = week_ago_datetime.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
        
        # Получаем токен доступа
        access_token = get_access_token(client_id, client_secret)
        
        if not access_token:
            logger.error("Не удалось получить токен доступа")
            return {
                "period": period,
                "calls": {"total": 0, "answered": 0, "missed": 0},
                "chats": {"total": 0},
                "phones_received": 0,
                "rating": 0,
                "reviews": {"total": 0, "weekly": 0},
                "items": {"total": 0, "with_xl_promotion": 0},
                "statistics": {"views": 0, "contacts": 0, "favorites": 0},
                "balance_real": 0,
                "balance_bonus": 0,
                "advance": 0,
                "expenses": {"total": 0, "details": {}}
            }
            
        # Получаем ID пользователя
        user_id = get_avito_user_id(client_id, client_secret)
        
        if not user_id:
            logger.error("Не удалось получить ID пользователя")
            return {
                "period": period,
                "calls": {"total": 0, "answered": 0, "missed": 0},
                "chats": {"total": 0},
                "phones_received": 0,
                "rating": 0,
                "reviews": {"total": 0, "weekly": 0},
                "items": {"total": 0, "with_xl_promotion": 0},
                "statistics": {"views": 0, "contacts": 0, "favorites": 0},
                "balance_real": 0,
                "balance_bonus": 0,
                "advance": 0,
                "expenses": {"total": 0, "details": {}}
            }
        
        # Получаем звонки за неделю
        calls_data = get_user_calls(access_token, week_start)
        total_calls = len(calls_data.get('calls', []))
        missed_calls = get_missed_calls(access_token, week_start)
        answered_calls = total_calls - missed_calls
        
        # Получаем новые чаты за неделю
        new_chats = get_chats_by_time(access_token, week_start)
        
        # Получаем историю показов телефона
        phones_received = get_all_numbers(access_token, week_start)
        
        # Получаем рейтинг пользователя
        rating = get_user_rating_info(access_token)
        
        # Получаем отзывы
        reviews_data = get_user_reviews(access_token, week_start)
        total_reviews = reviews_data.get('total_reviews', 0)
        weekly_reviews = reviews_data.get('period_reviews', 0)
        
        # Получаем данные о объявлениях
        item_ids = get_user_items_stats(access_token, user_id)
        promotion_info = get_item_promotion_info(access_token, user_id, item_ids)
        
        # Получаем статистику объявлений
        items_stats = get_items_statistics(access_token, user_id, item_ids, week_start)
        
        # Получаем информацию о балансе
        balance_info = get_user_balance_info(access_token, user_id)
        
        # Получаем данные о расходах за неделю с использованием обновленной функции
        expenses = get_weekly_expenses(access_token)
        
        # Формируем результат
        result = {
            "period": period,
            "calls": {
                "total": total_calls,
                "answered": answered_calls,
                "missed": missed_calls
            },
            "chats": {
                "total": new_chats
            },
            "phones_received": phones_received,
            "rating": rating,
            "reviews": {
                "total": total_reviews,
                "weekly": weekly_reviews
            },
            "items": {
                "total": promotion_info.get('total_items', 0),
                "with_xl_promotion": promotion_info.get('xl_promotion_count', 0)
            },
            "statistics": {
                "views": items_stats.get('total_views', 0),
                "contacts": items_stats.get('total_contacts', 0),
                "favorites": items_stats.get('total_favorites', 0)
            },
            "balance_real": balance_info.get('balance_real', 0),
            "balance_bonus": balance_info.get('balance_bonus', 0),
            "advance": balance_info.get('advance', 0),
            "expenses": expenses
        }
        
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении недельной статистики: {e}")
        current_datetime = datetime.datetime.now()
        current_date = current_datetime.strftime("%d.%m.%Y")
        week_ago_date = (current_datetime - datetime.timedelta(days=7)).strftime("%d.%m.%Y")
        period = f"{week_ago_date} - {current_date}"
        
        return {
            "period": period,
            "calls": {"total": 0, "answered": 0, "missed": 0},
            "chats": {"total": 0},
            "phones_received": 0,
            "rating": 0,
            "reviews": {"total": 0, "weekly": 0},
            "items": {"total": 0, "with_xl_promotion": 0},
            "statistics": {"views": 0, "contacts": 0, "favorites": 0},
            "balance_real": 0,
            "balance_bonus": 0,
            "advance": 0,
            "expenses": {"total": 0, "details": {}}
        } 