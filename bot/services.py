import requests
import json
import datetime
import logging

logger = logging.getLogger(__name__)

def get_access_token(client_id, client_secret):
    auth_url = 'https://api.avito.ru/token'
    auth_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }

    auth_response = requests.post(auth_url, data=auth_data)
    auth_result = json.loads(auth_response.text)

    # Извлечение API ключа из ответа
    access_token = auth_result.get('access_token')
    return access_token

def get_user_calls(access_token, date_from=None, date_to=None):
    # Получение списка звонков за указанный период
    if date_from is None or date_to is None:
        current_time = datetime.datetime.now()
        date_from = (current_time - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
        date_to = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")

    calls_url = 'https://api.avito.ru/calltracking/v1/getCalls/'
    calls_data = {
        'dateTimeFrom': date_from,
        'dateTimeTo': date_to,
        'limit': 100,
        'offset': 0
    }
    headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }

    calls_response = requests.post(calls_url, headers=headers, json=calls_data)
    calls_result = json.loads(calls_response.text)
    return calls_result


def get_total_calls(access_token, date_from=None, date_to=None):
    calls_result = get_user_calls(access_token, date_from, date_to)
    total_calls = len(calls_result.get('calls', []))
    return total_calls

def get_missed_calls(access_token, date_from=None, date_to=None):
    calls_result = get_user_calls(access_token, date_from, date_to)
    missed_calls = sum(1 for call in calls_result.get('calls', []) if call.get('talkDuration', 0) == 0)
    return missed_calls

def get_user_balance_info(access_token, user_id=None):
    """
    Получает подробную информацию о балансе пользователя:
    - balance_real - реальные деньги в кошельке
    - balance_bonus - бонусные средства
    - advance - авансовые платежи (бывший 'balance' из API v3)
    """
    try:
        # Если не передан user_id, получаем его из профиля
        if not user_id:
            profile_url = 'https://api.avito.ru/core/v1/accounts/self'
            profile_headers = {
                'Authorization': f'Bearer {access_token}'
            }
            profile_response = requests.get(profile_url, headers=profile_headers)
            profile_response.raise_for_status()
            profile_data = profile_response.json()
            user_id = profile_data.get('id')
            
            if not user_id:
                logger.error("Не удалось получить идентификатор пользователя")
                return {"balance_real": 0, "balance_bonus": 0, "advance": 0}
        
        # Получаем реальный баланс кошелька (метод API v1)
        balance_url = f'https://api.avito.ru/core/v1/accounts/{user_id}/balance/'
        balance_headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        balance_response = requests.get(balance_url, headers=balance_headers)
        balance_response.raise_for_status()
        balance_data = balance_response.json()
        
        # Получаем авансы (старый метод API v3)
        advance_url = 'https://api.avito.ru/cpa/v3/balanceInfo'
        advance_headers = {
            'Authorization': f'Bearer {access_token}',
            'X-Source': 'python_script',
            'Content-Type': 'application/json'
        }
        advance_data = {}
        
        advance_response = requests.post(advance_url, headers=advance_headers, json=advance_data)
        advance_response.raise_for_status()
        advance_result = advance_response.json()
        
        # Получаем данные о авансе из ответа API
        advance = 0
        if 'balance' in advance_result:
            advance = advance_result['balance'] / 100
        elif 'data' in advance_result and 'balance' in advance_result['data']:
            advance = advance_result['data']['balance'] / 100
        
        # Формируем ответ с полной информацией о балансе
        return {
            "balance_real": balance_data.get('real', 0),  # Реальные деньги
            "balance_bonus": balance_data.get('bonus', 0),  # Бонусы
            "advance": advance  # Авансовые платежи (старый 'balance')
        }
    except Exception as e:
        logger.error(f"Ошибка при получении информации о балансе: {e}")
        return {"balance_real": 0, "balance_bonus": 0, "advance": 0}

# Оставляем старую функцию для обратной совместимости, но теперь она возвращает авансы
def get_user_ballance(access_token):
    """Устаревшая функция, возвращает авансовые платежи для обратной совместимости"""
    try:
        balance_info = get_user_balance_info(access_token)
        return balance_info['advance']
    except Exception as e:
        logger.error(f"Ошибка при получении аванса: {e}")
        return 0

def get_user_chats(access_token, date_from=None, date_to=None, unread_only=False, chat_types=None, limit=100, offset=0):
    """Получение списка чатов пользователя за определенный период"""
    # Получаем user_id из профиля пользователя
    try:
        profile_url = 'https://api.avito.ru/core/v1/accounts/self'
        profile_headers = {
            'Authorization': f'Bearer {access_token}'
        }
        profile_response = requests.get(profile_url, headers=profile_headers)
        profile_response.raise_for_status()
        profile_data = profile_response.json()
        user_id = profile_data.get('id')
        
        if not user_id:
            logger.error("Не удалось получить идентификатор пользователя")
            return 0
            
        # Формируем URL для получения чатов
        chats_url = f'https://api.avito.ru/messenger/v2/accounts/{user_id}/chats'
        
        # Параметры запроса
        params = {
            'limit': limit,
            'offset': offset
        }
        
        # Добавляем параметры периода, если они указаны
        if date_from:
            params['date_from'] = date_from
            
        if date_to:
            params['date_to'] = date_to
        
        # Добавляем необязательные параметры, если они указаны
        if unread_only:
            params['unread_only'] = 'true'
            
        if chat_types:
            params['chat_types'] = ','.join(chat_types)
        else:
            params['chat_types'] = 'u2i'  # По умолчанию только чаты по объявлениям
        
        # Заголовки запроса
        headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        # Выполняем запрос
        chats_response = requests.get(chats_url, headers=headers, params=params)
        chats_response.raise_for_status()
        chats_result = chats_response.json()
        # Возвращаем количество чатов
        total_chats = len(chats_result.get('chats', []))
        return total_chats
        
    except Exception as e:
        logger.error(f"Ошибка при получении списка чатов: {e}")
        return 0

def get_all_numbers(access_token, date_from=None, date_to=None):
    if date_from is None:
        current_time = datetime.datetime.now()
        date_from = (current_time - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    phones_url = 'https://api.avito.ru/cpa/v1/phonesInfoFromChats'
    phones_data = {
        'dateTimeFrom': date_from,
        'limit': 100,
        'offset': 0
    }
    phones_headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Source': 'python_script',
        'Content-Type': 'application/json'
    }

    phones_response = requests.post(phones_url, headers=phones_headers, json=phones_data)
    phones_result = json.loads(phones_response.text)
    total_phone_results = phones_result.get('total', 0)
    return total_phone_results


def get_user_items_stats(access_token, user_id, status="active", per_page=25, page=1, date_from=None, date_to=None, period_grouping="day"):
    """Получает базовую информацию о объявлениях пользователя и их идентификаторы."""
    items_url = 'https://api.avito.ru/core/v1/items'
    items_headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    params = {
        'status': status,
        'per_page': per_page,
        'page': page
    }
    
    response = requests.get(items_url, headers=items_headers, params=params)
    result = json.loads(response.text)
    
    # Правильное извлечение идентификаторов объявлений из структуры ответа API
    item_ids = [item['id'] for item in result.get('resources', [])]
    
    return item_ids

def get_item_promotion_info(access_token, user_id, item_ids):
    """Получает информацию о продвижении объявлений."""
    # Подсчет объявлений с XL продвижением
    xl_promotion_count = 0
    
    # Получаем детальную информацию о каждом объявлении для проверки XL продвижения
    for item_id in item_ids:
        item_info_url = f'https://api.avito.ru/core/v1/accounts/{user_id}/items/{item_id}/'
        item_info_headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        try:
            item_response = requests.get(item_info_url, headers=item_info_headers)
            item_data = json.loads(item_response.text)
            # Здесь можно добавить логику для подсчета XL продвижений
        except Exception as e:
            # Логирование ошибки вместо вывода на экран
            pass
    
    return {
        "total_items": len(item_ids),
        "xl_promotion_count": xl_promotion_count
    }

def get_items_statistics(access_token, user_id, item_ids, date_from=None, date_to=None, period_grouping="day"):
    """Получает статистику по объявлениям: просмотры, контакты, избранное."""
    if not item_ids:
        return {
            "total_views": 0,
            "total_contacts": 0,
            "total_favorites": 0
        }
        
    # Получение статистики по объявлениям
    stats_url = f'https://api.avito.ru/stats/v1/accounts/{user_id}/items'
    stats_headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    stats_data = {
        'dateFrom': date_from,
        'dateTo': date_to,
        'itemIds': item_ids[:200],  # Ограничиваем до 200 идентификаторов
        'fields': ["uniqViews", "uniqContacts", "uniqFavorites"],
        'periodGrouping': period_grouping
    }
    
    stats_response = requests.post(stats_url, headers=stats_headers, json=stats_data)
    stats_result = json.loads(stats_response.text)
    
    # Подсчет общего количества просмотров, контактов и избранных
    total_views = 0
    total_contacts = 0
    total_favorites = 0
    
    for item in stats_result.get('result', {}).get('items', []):
        for stat in item.get('stats', []):
            total_views += stat.get('uniqViews', 0)
            total_contacts += stat.get('uniqContacts', 0)
            total_favorites += stat.get('uniqFavorites', 0)
    
    return {
        "total_views": total_views,
        "total_contacts": total_contacts,
        "total_favorites": total_favorites
    }


def get_user_rating_info(access_token):
    rating_info_url = 'https://api.avito.ru/ratings/v1/info'
    rating_info_headers = {
        'Authorization': f'Bearer {access_token}'
    }

    response = requests.get(rating_info_url, headers=rating_info_headers)
    result = json.loads(response.text)
    score = result.get('rating', {}).get('score', 0)
    return score


def get_user_reviews(access_token, date_from=None, date_to=None, offset=0, limit=50):
    reviews_url = 'https://api.avito.ru/ratings/v1/reviews'
    reviews_headers = {
        'Authorization': f'Bearer {access_token}'
    }

    params = {
        'offset': offset,
        'limit': limit
    }

    response = requests.get(reviews_url, headers=reviews_headers, params=params)
    result = json.loads(response.text)

    total_reviews = result.get('total', 0)
    reviews = result.get('reviews', [])

    # Подсчет отзывов за указанный период
    today_reviews = 0

    if date_from is None:
        today = datetime.datetime.now().date()
        for review in reviews:
            review_date = datetime.datetime.fromtimestamp(review.get('createdAt', 0)).date()
            if review_date == today:
                today_reviews += 1
    else:
        date_from_obj = datetime.datetime.strptime(date_from.split('T')[0], "%Y-%m-%d").date()
        date_to_obj = datetime.datetime.strptime(date_to.split('T')[0], "%Y-%m-%d").date() if date_to else datetime.datetime.now().date()
        
        for review in reviews:
            review_date = datetime.datetime.fromtimestamp(review.get('createdAt', 0)).date()
            if date_from_obj <= review_date <= date_to_obj:
                today_reviews += 1

    return {
        "total_reviews": total_reviews,
        "period_reviews": today_reviews
    }





def get_avito_user_id(client_id, client_secret):
    token_url = 'https://api.avito.ru/token'
    token_data = {
        'grant_type': 'client_credentials',
        'client_id': client_id,
        'client_secret': client_secret
    }
    
    try:
        # Получаем токен доступа
        token_response = requests.post(token_url, data=token_data)
        token_response.raise_for_status()
        token_result = token_response.json()
        access_token = token_result.get('access_token')
        
        if not access_token:
            return None
            
        # Получаем информацию о пользователе
        user_info_url = 'https://api.avito.ru/core/v1/accounts/self'
        user_info_headers = {
            'Authorization': f'Bearer {access_token}'
        }
        
        user_response = requests.get(user_info_url, headers=user_info_headers)
        user_response.raise_for_status()
        user_data = user_response.json()
        
        # Возвращаем Avito ID пользователя
        return user_data.get('id')
    except Exception as e:
        print(f"Ошибка при получении Avito ID: {e}")
        return None



def get_daily_statistics(client_id, client_secret):
    try:
        # Получаем текущую дату
        current_time = datetime.datetime.now()
        today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
        today_end = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        logger.info(f"Запрос дневной статистики с {today_start} по {today_end}")
        
        # Получаем токен доступа
        access_token = get_access_token(client_id, client_secret)
        if not access_token:
            logger.error("Не удалось получить токен доступа")
            raise Exception("Не удалось получить токен доступа")
            
        user_id = get_avito_user_id(client_id, client_secret)
        if not user_id:
            logger.error("Не удалось получить ID пользователя")
            raise Exception("Не удалось получить ID пользователя")
        
        # Инициализируем значения по умолчанию
        total_calls = 0
        missed_calls = 0
        balance_info = {"balance_real": 0, "balance_bonus": 0, "advance": 0}
        expenses_info = {"total": 0, "details": {}}
        total_chats = 0
        total_phones = 0
        rating = 0
        reviews_info = {"total_reviews": 0, "period_reviews": 0}
        promotion_info = {"total_items": 0, "xl_promotion_count": 0}
        items_stats = {"total_views": 0, "total_contacts": 0, "total_favorites": 0}
        
        try:
            # Получаем статистику звонков
            total_calls = get_total_calls(access_token, today_start, today_end)
            missed_calls = get_missed_calls(access_token, today_start, today_end)
        except Exception as e:
            logger.error(f"Ошибка при получении статистики звонков: {e}")
        
        try:
            # Получаем полную информацию о балансе
            balance_info = get_user_balance_info(access_token, user_id)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о балансе: {e}")
        
        try:
            # Получаем информацию о расходах
            expenses_info = get_daily_expenses(access_token)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о расходах: {e}")
        
        try:
            # Получаем чаты и показы телефона
            total_chats = get_user_chats(access_token, today_start, today_end)
            total_phones = get_all_numbers(access_token, today_start, today_end)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о чатах и телефонах: {e}")
        
        try:
            # Получаем рейтинг и отзывы
            rating = get_user_rating_info(access_token)
            reviews_info = get_user_reviews(access_token, today_start, today_end)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о рейтинге и отзывах: {e}")
        
        try:
            # Получаем информацию о объявлениях
            item_ids = get_user_items_stats(access_token, user_id, date_from=today_start, date_to=today_end)
            promotion_info = get_item_promotion_info(access_token, user_id, item_ids)
            items_stats = get_items_statistics(access_token, user_id, item_ids, date_from=today_start, date_to=today_end)
        except Exception as e:
            logger.error(f"Ошибка при получении информации об объявлениях: {e}")
        
        # Формируем и возвращаем полную статистику за день
        result = {
            "date": current_time.strftime("%Y-%m-%d"),
            "calls": {
                "total": total_calls,
                "missed": missed_calls,
                "answered": total_calls - missed_calls
            },
            "balance_real": balance_info["balance_real"],
            "balance_bonus": balance_info["balance_bonus"],
            "advance": balance_info["advance"],
            "expenses": expenses_info,
            "chats": total_chats,
            "phones_received": total_phones,
            "rating": rating,
            "reviews": {
                "total": reviews_info["total_reviews"],
                "today": reviews_info["period_reviews"]
            },
            "items": {
                "total": promotion_info["total_items"],
                "with_xl_promotion": promotion_info["xl_promotion_count"]
            },
            "statistics": {
                "views": items_stats["total_views"],
                "contacts": items_stats["total_contacts"],
                "favorites": items_stats["total_favorites"]
            }
        }
        
        logger.info(f"Дневная статистика успешно получена")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении дневной статистики: {e}")
        # Возвращаем структуру с нулевыми значениями в случае ошибки
        return {
            "date": current_time.strftime("%Y-%m-%d"),
            "calls": {"total": 0, "missed": 0, "answered": 0},
            "balance_real": 0,
            "balance_bonus": 0,
            "advance": 0,
            "expenses": {"total": 0, "details": {}},
            "chats": 0,
            "phones_received": 0,
            "rating": 0,
            "reviews": {"total": 0, "today": 0},
            "items": {"total": 0, "with_xl_promotion": 0},
            "statistics": {"views": 0, "contacts": 0, "favorites": 0}
        }


def get_weekly_statistics(client_id, client_secret):
    try:
        # Получаем текущую дату и дату неделю назад
        current_time = datetime.datetime.now()
        week_ago = current_time - datetime.timedelta(days=7)
        week_start = week_ago.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
        week_end = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
        
        logger.info(f"Запрос недельной статистики с {week_start} по {week_end}")
        
        # Получаем токен доступа
        access_token = get_access_token(client_id, client_secret)
        if not access_token:
            logger.error("Не удалось получить токен доступа")
            raise Exception("Не удалось получить токен доступа")
            
        user_id = get_avito_user_id(client_id, client_secret)
        if not user_id:
            logger.error("Не удалось получить ID пользователя")
            raise Exception("Не удалось получить ID пользователя")
        
        # Инициализируем значения по умолчанию
        total_calls = 0
        missed_calls = 0
        balance_info = {"balance_real": 0, "balance_bonus": 0, "advance": 0}
        expenses_info = {"total": 0, "details": {}}
        total_chats = 0
        total_phones = 0
        rating = 0
        reviews_info = {"total_reviews": 0, "period_reviews": 0}
        promotion_info = {"total_items": 0, "xl_promotion_count": 0}
        items_stats = {"total_views": 0, "total_contacts": 0, "total_favorites": 0}
        
        try:
            # Получаем статистику звонков
            total_calls = get_total_calls(access_token, week_start, week_end)
            missed_calls = get_missed_calls(access_token, week_start, week_end)
        except Exception as e:
            logger.error(f"Ошибка при получении статистики звонков: {e}")
        
        try:
            # Получаем полную информацию о балансе
            balance_info = get_user_balance_info(access_token, user_id)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о балансе: {e}")
        
        try:
            # Получаем информацию о расходах
            expenses_info = get_weekly_expenses(access_token)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о расходах: {e}")
        
        try:
            # Получаем чаты и показы телефона
            total_chats = get_user_chats(access_token, week_start, week_end)
            total_phones = get_all_numbers(access_token, week_start, week_end)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о чатах и телефонах: {e}")
        
        try:
            # Получаем рейтинг и отзывы
            rating = get_user_rating_info(access_token)
            reviews_info = get_user_reviews(access_token, week_start, week_end)
        except Exception as e:
            logger.error(f"Ошибка при получении информации о рейтинге и отзывах: {e}")
        
        try:
            # Получаем информацию о объявлениях
            item_ids = get_user_items_stats(access_token, user_id, date_from=week_start, date_to=week_end)
            promotion_info = get_item_promotion_info(access_token, user_id, item_ids)
            items_stats = get_items_statistics(access_token, user_id, item_ids, date_from=week_start, date_to=week_end)
        except Exception as e:
            logger.error(f"Ошибка при получении информации об объявлениях: {e}")
        
        # Формируем и возвращаем полную статистику за неделю
        result = {
            "period": f"{week_ago.strftime('%Y-%m-%d')} - {current_time.strftime('%Y-%m-%d')}",
            "calls": {
                "total": total_calls,
                "missed": missed_calls,
                "answered": total_calls - missed_calls
            },
            "balance_real": balance_info["balance_real"],
            "balance_bonus": balance_info["balance_bonus"],
            "advance": balance_info["advance"],
            "expenses": expenses_info,
            "chats": total_chats,
            "phones_received": total_phones,
            "rating": rating,
            "reviews": {
                "total": reviews_info["total_reviews"],
                "weekly": reviews_info["period_reviews"]
            },
            "items": {
                "total": promotion_info["total_items"],
                "with_xl_promotion": promotion_info["xl_promotion_count"]
            },
            "statistics": {
                "views": items_stats["total_views"],
                "contacts": items_stats["total_contacts"],
                "favorites": items_stats["total_favorites"]
            }
        }
        
        logger.info(f"Недельная статистика успешно получена")
        return result
        
    except Exception as e:
        logger.error(f"Ошибка при получении недельной статистики: {e}")
        # Возвращаем структуру с нулевыми значениями в случае ошибки
        return {
            "period": f"{week_ago.strftime('%Y-%m-%d')} - {current_time.strftime('%Y-%m-%d')}",
            "calls": {"total": 0, "missed": 0, "answered": 0},
            "balance_real": 0,
            "balance_bonus": 0,
            "advance": 0,
            "expenses": {"total": 0, "details": {}},
            "chats": 0,
            "phones_received": 0,
            "rating": 0,
            "reviews": {"total": 0, "weekly": 0},
            "items": {"total": 0, "with_xl_promotion": 0},
            "statistics": {"views": 0, "contacts": 0, "favorites": 0}
        }

def update_user_chats_count(user, access_token=None):
    """Обновляет счетчики чатов пользователя и возвращает количество новых чатов"""
    if not access_token:
        access_token = get_access_token(user.client_id, user.client_secret)
        if not access_token:
            logger.error(f"Не удалось получить токен доступа для пользователя {user.telegram_id}")
            return 0
    
    try:
        # Получаем текущее количество чатов
        current_chat_count = get_user_chats(access_token)
        
        # Если это первый запрос (чаты еще не считались) или поле не инициализировано
        if not hasattr(user, 'day_chats') or user.day_chats is None:
            user.day_chats = 0
            
        if not hasattr(user, 'week_chats') or user.week_chats is None:
            user.week_chats = 0
            
        # Если счетчики нулевые, просто сохраняем текущее значение
        if user.day_chats == 0:
            user.day_chats = current_chat_count
            user.week_chats = current_chat_count
            user.save()
            return 0
        
        # Определяем количество новых чатов за день
        new_day_chats = current_chat_count - user.day_chats
        if new_day_chats > 0:
            # Обновляем счетчики
            user.day_chats = current_chat_count
            user.week_chats += new_day_chats  # Добавляем новые чаты к недельному счетчику
            user.save()
            return new_day_chats
        
        return 0
    except Exception as e:
        logger.error(f"Ошибка при обновлении счетчиков чатов: {e}")
        return 0

def get_operations_history(access_token, date_from, date_to):
    """
    Получает историю операций пользователя за указанный период
    и возвращает детализацию расходов.
    
    Args:
        access_token: Токен доступа к API
        date_from: Начало периода в формате строки ISO (например, '2023-04-01T00:00:00Z')
        date_to: Конец периода в формате строки ISO (например, '2023-04-08T00:00:00Z')
        
    Returns:
        dict: Словарь с общей суммой расходов и детализацией по типам услуг
    """
    try:
        # URL для получения истории операций
        operations_url = 'https://api.avito.ru/core/v1/accounts/operations_history/'
        
        # Заголовки запроса
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }
        
        # Данные запроса
        data = {
            'dateTimeFrom': date_from,
            'dateTimeTo': date_to
        }
        
        logger.info(f"Запрос истории операций с {date_from} по {date_to}")
        
        # Выполняем запрос
        response = requests.post(operations_url, headers=headers, json=data)
        print(response.text)
        response.raise_for_status()
        
        # Проверяем, что ответ не пустой
        if not response.text.strip():
            logger.error("Получен пустой ответ от API операций")
            return {'total': 0, 'details': {}}
            
        # Парсим JSON ответ
        try:
            result = response.json()
            logger.info(f"Получен ответ от API операций")
        except json.JSONDecodeError as e:
            logger.error(f"Ошибка декодирования JSON: {e}, содержимое ответа: {response.text}")
            return {'total': 0, 'details': {}}
        
        # Инициализируем счетчики и структуру для детализации расходов
        total_expenses = 0
        expenses_details = {}
        
        # Обрабатываем все операции
        for operation in result.get('operations', []):
            # Тип операции
            operation_type = operation.get('operationType', '')
            
            # Считаем только операции расхода средств
            expense_types = [
                'резервирование средств под услугу',
                'списание за услугу',
                'резервирование средств',
                'списание средств'
            ]
            
            if operation_type.lower() not in [t.lower() for t in expense_types]:
                continue
                
            # Получаем сумму расхода
            amount_rub = operation.get('amountRub', 0)
            if amount_rub <= 0:
                continue
                
            # Добавляем в общую сумму расходов
            total_expenses += amount_rub
            
            # Получаем информацию о типе услуги
            service_name = operation.get('serviceName', 'Неизвестно')
            operation_name = operation.get('operationName', 'Неизвестно')
            service_type = operation.get('serviceType', 'Неизвестно')
            item_id = operation.get('itemId', 'Неизвестно')
            
            # Формируем ключ для группировки
            key = f"{service_name} ({service_type})"
            
            # Добавляем или обновляем запись в детализации
            if key in expenses_details:
                expenses_details[key]['amount'] += amount_rub
                expenses_details[key]['count'] += 1
                expenses_details[key]['items'].add(str(item_id))
            else:
                expenses_details[key] = {
                    'amount': amount_rub,
                    'count': 1,
                    'type': operation_type,
                    'items': {str(item_id)} if item_id != 'Неизвестно' else set()
                }
        
        # Преобразуем множества объявлений в списки для сериализации JSON
        for key in expenses_details:
            expenses_details[key]['items'] = list(expenses_details[key]['items'])
            if len(expenses_details[key]['items']) == 1 and expenses_details[key]['items'][0] == 'Неизвестно':
                expenses_details[key]['items'] = []
        
        # Формируем структуру с результатами
        result = {
            'total': total_expenses,
            'details': expenses_details
        }
        
        logger.info(f"Расходы за период: общая сумма {total_expenses:.2f} руб., {len(expenses_details)} категорий")
        return result
    except Exception as e:
        logger.error(f"Ошибка при получении истории операций: {e}")
        return {
            'total': 0,
            'details': {}
        }

def get_daily_expenses(access_token):
    """Получает расходы за текущий день"""
    # Получаем текущую дату и начало дня
    current_time = datetime.datetime.now()
    day_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    current_iso = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    logger.info(f"Запрос дневных расходов с {day_start} по {current_iso}")
    
    # Получаем расходы
    return get_operations_history(access_token, day_start, current_iso)

def get_weekly_expenses(access_token):
    """Получает расходы за текущую неделю"""
    # Получаем текущую дату и начало недели (7 дней назад)
    current_time = datetime.datetime.now()
    week_start = (current_time - datetime.timedelta(days=7)).replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    current_iso = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    logger.info(f"Запрос недельных расходов с {week_start} по {current_iso}")
    
    # Получаем расходы
    return get_operations_history(access_token, week_start, current_iso)