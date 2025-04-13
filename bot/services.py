import requests
import json
import datetime


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

def get_user_ballance(access_token):
    balance_url = 'https://api.avito.ru/cpa/v3/balanceInfo'
    balance_headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Source': 'python_script',
        'Content-Type': 'application/json'
    }
    balance_data = {}

    balance_response = requests.post(balance_url, headers=balance_headers, json=balance_data)
    balance_result = json.loads(balance_response.text)
    return balance_result.get('balance', 0) / 100

def get_user_chats(access_token, date_from=None, date_to=None):
    # Получение списка чатов за указанный период
    if date_from is None:
        current_time = datetime.datetime.now()
        date_from = (current_time - datetime.timedelta(days=30)).strftime("%Y-%m-%dT%H:%M:%SZ")
    
    chats_url = 'https://api.avito.ru/cpa/v2/chatsByTime'
    chats_data = {
        'dateTimeFrom': date_from,
        'limit': 100,
        'offset': 0
    }
    chats_headers = {
        'Authorization': f'Bearer {access_token}',
        'X-Source': 'python_script',
        'Content-Type': 'application/json'
    }

    chats_response = requests.post(chats_url, headers=chats_headers, json=chats_data)
    chats_result = json.loads(chats_response.text)
    total_chats = len(chats_result.get('chats', []))
    return total_chats

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
    # Получаем текущую дату
    current_time = datetime.datetime.now()
    today_start = current_time.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    today_end = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Получаем токен доступа (предполагается, что client_id и client_secret доступны)
    access_token = get_access_token(client_id, client_secret)
    user_id = get_avito_user_id(client_id, client_secret)
    
    # Получаем статистику за сегодня
    total_calls = get_total_calls(access_token, today_start, today_end)
    missed_calls = get_missed_calls(access_token, today_start, today_end)
    balance = get_user_ballance(access_token)
    total_chats = get_user_chats(access_token, today_start, today_end)
    total_phones = get_all_numbers(access_token, today_start, today_end)
    rating = get_user_rating_info(access_token)
    reviews_info = get_user_reviews(access_token, today_start, today_end)
    
    # Получаем информацию о объявлениях
    item_ids = get_user_items_stats(access_token, user_id, date_from=today_start, date_to=today_end)
    promotion_info = get_item_promotion_info(access_token, user_id, item_ids)
    items_stats = get_items_statistics(access_token, user_id, item_ids, date_from=today_start, date_to=today_end)
    
    # Формируем и возвращаем полную статистику за день
    return {
        "date": current_time.strftime("%Y-%m-%d"),
        "calls": {
            "total": total_calls,
            "missed": missed_calls,
            "answered": total_calls - missed_calls
        },
        "balance": balance,
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


def get_weekly_statistics(client_id, client_secret):
    # Получаем текущую дату и дату неделю назад
    current_time = datetime.datetime.now()
    week_ago = current_time - datetime.timedelta(days=7)
    week_start = week_ago.replace(hour=0, minute=0, second=0, microsecond=0).strftime("%Y-%m-%dT%H:%M:%SZ")
    week_end = current_time.strftime("%Y-%m-%dT%H:%M:%SZ")
    
    # Получаем токен доступа (предполагается, что client_id и client_secret доступны)
    access_token = get_access_token(client_id, client_secret)
    user_id = get_avito_user_id(client_id, client_secret)
    
    # Получаем статистику за неделю
    total_calls = get_total_calls(access_token, week_start, week_end)
    missed_calls = get_missed_calls(access_token, week_start, week_end)
    balance = get_user_ballance(access_token)
    total_chats = get_user_chats(access_token, week_start, week_end)
    total_phones = get_all_numbers(access_token, week_start, week_end)
    rating = get_user_rating_info(access_token)
    reviews_info = get_user_reviews(access_token, week_start, week_end)
    
    # Получаем информацию о объявлениях
    item_ids = get_user_items_stats(access_token, user_id, date_from=week_start, date_to=week_end)
    promotion_info = get_item_promotion_info(access_token, user_id, item_ids)
    items_stats = get_items_statistics(access_token, user_id, item_ids, date_from=week_start, date_to=week_end)
    
    # Формируем и возвращаем полную статистику за неделю
    return {
        "period": f"{week_ago.strftime('%Y-%m-%d')} - {current_time.strftime('%Y-%m-%d')}",
        "calls": {
            "total": total_calls,
            "missed": missed_calls,
            "answered": total_calls - missed_calls
        },
        "balance": balance,
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