import requests
import json
import datetime


# Получение API ключа с использованием client_id и client_secret
client_id = 'kKQ5kxCxhcKoqw2oRx2V'
client_secret = 'Y9C7tgtwP0uNLqoA5g5WR0GkoqkGzDJZwdroCnZ7'

# Запрос на получение токена доступа (API ключа)
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

# Получение списка звонков за последний месяц
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

# Подсчет общего количества звонков и неотвеченных звонков
total_calls = len(calls_result.get('calls', []))
missed_calls = sum(1 for call in calls_result.get('calls', []) if call.get('talkDuration', 0) == 0)

print(f"Всего звонков: {total_calls}")
print(f"Неотвеченных звонков: {missed_calls}")

# Получение информации о балансе пользователя
balance_url = 'https://api.avito.ru/cpa/v3/balanceInfo'
balance_headers = {
    'Authorization': f'Bearer {access_token}',
    'X-Source': 'python_script',
    'Content-Type': 'application/json'
}
balance_data = {}

balance_response = requests.post(balance_url, headers=balance_headers, json=balance_data)
balance_result = json.loads(balance_response.text)
print(f"Баланс пользователя: {balance_result.get('balance', 0) / 100} руб.")

# Получение списка чатов
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
print(f"Всего чатов: {total_chats}")

# Получение информации о номерах телефонов из целевых чатов
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
print(f"Всего номеров телефонов из целевых чатов: {total_phone_results}")

# Получение статистики по объявлениям
def get_items_stats(user_id, item_ids, date_from, date_to, fields=None, period_grouping="day"):
    stats_url = f'https://api.avito.ru/stats/v1/accounts/{user_id}/items'
    stats_headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    if fields is None:
        fields = ["uniqViews", "uniqContacts", "uniqFavorites"]
    
    stats_data = {
        'dateFrom': date_from,
        'dateTo': date_to,
        'itemIds': item_ids,
        'fields': fields,
        'periodGrouping': period_grouping
    }
    
    response = requests.post(stats_url, headers=stats_headers, json=stats_data)
    result = json.loads(response.text)
    print(f"Статистика по объявлениям: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

# Получение статистики по звонкам
def get_calls_stats(user_id, date_from, date_to, item_ids=None):
    calls_stats_url = f'https://api.avito.ru/core/v1/accounts/{user_id}/calls/stats/'
    calls_stats_headers = {
        'Authorization': f'Bearer {access_token}',
        'Content-Type': 'application/json'
    }
    
    calls_stats_data = {
        'dateFrom': date_from,
        'dateTo': date_to
    }
    
    if item_ids:
        calls_stats_data['itemIds'] = item_ids
    
    response = requests.post(calls_stats_url, headers=calls_stats_headers, json=calls_stats_data)
    result = json.loads(response.text)
    print(f"Статистика по звонкам: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

# Получение информации по объявлению
def get_item_info(user_id, item_id):
    item_info_url = f'https://api.avito.ru/core/v1/accounts/{user_id}/items/{item_id}/'
    item_info_headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(item_info_url, headers=item_info_headers)
    result = json.loads(response.text)
    print(f"Информация по объявлению {item_id}: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result

# Получение информации по объявлениям пользователя и статистики по ним
def get_user_items_stats(user_id, status="active", per_page=25, page=1, date_from=None, date_to=None, period_grouping="day"):
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
    

    if item_ids:
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
        
        print(f"Общее количество просмотров: {total_views}")
        print(f"Общее количество контактов: {total_contacts}")
        print(f"Общее количество добавлений в избранное: {total_favorites}")

# Получение информации о рейтинге пользователя
def get_user_rating_info():
    rating_info_url = 'https://api.avito.ru/ratings/v1/info'
    rating_info_headers = {
        'Authorization': f'Bearer {access_token}'
    }
    
    response = requests.get(rating_info_url, headers=rating_info_headers)
    result = json.loads(response.text)
    score = result.get('rating', {}).get('score', 0)
    print(f"Рейтинг пользователя: {score} звезд")
    return result

# Получение списка отзывов о пользователе
def get_user_reviews(offset=0, limit=50):
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
    
    # Подсчет отзывов за сегодня
    today = datetime.datetime.now().date()
    today_reviews = 0
    
    for review in reviews:
        review_date = datetime.datetime.fromtimestamp(review.get('createdAt', 0)).date()
        if review_date == today:
            today_reviews += 1
    
    print(f"Всего отзывов о пользователе: {total_reviews}")
    print(f"Получено отзывов за сегодня: {today_reviews}")
    
    return result


# Пример вызова функций
get_user_items_stats(user_id='81070063', date_from='2025-04-12', date_to='2025-04-12')
get_user_rating_info()
get_user_reviews()
