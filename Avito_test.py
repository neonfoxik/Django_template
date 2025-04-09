import requests
import logging
from datetime import datetime, timedelta

# Настройка логирования
logger = logging.getLogger(__name__)

class AvitoAPI:
    """Класс для работы с API Авито"""
    BASE_URL = "https://api.avito.ru"
    TOKEN_URL = "https://api.avito.ru/token"
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.token = None
        self.token_expires_at = None
        
    def get_token(self):
        """Получение токена доступа через client_credentials flow"""
        if self.token and self.token_expires_at and datetime.now() < self.token_expires_at:
            logger.info("Используем существующий токен")
            return self.token
            
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        try:
            logger.info(f"Запрос токена для client_id {self.client_id}")
            response = requests.post(self.TOKEN_URL, data=data, headers=headers, timeout=10)
            logger.info(f"Ответ при запросе токена: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Ошибка получения токена: {response.status_code}, {response.text}")
                return None
                
            token_data = response.json()
            self.token = token_data.get('access_token')
            expires_in = token_data.get('expires_in', 86400)
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            if self.token:
                logger.info(f"Токен успешно получен, действителен до {self.token_expires_at}")
            else:
                logger.error(f"Токен не найден в ответе: {token_data}")
            return self.token
        except Exception as e:
            logger.error(f"Исключение при получении токена: {e}")
            return None
    
    def get(self, endpoint, params=None):
        """Выполнение GET-запроса к API"""
        if not self.token or (self.token_expires_at and datetime.now() >= self.token_expires_at):
            if not self.get_token():
                logger.error("Не удалось получить токен")
                return None
                
        headers = {
            "Authorization": f"Bearer {self.token}",
            "Content-Type": "application/json",
            "Accept": "application/json"
        }
        
        url = f"{self.BASE_URL}/{endpoint}"
        
        try:
            response = requests.get(url, headers=headers, params=params, timeout=10)
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка запроса: {response.status_code}, {response.text}")
                return None
        except Exception as e:
            logger.error(f"Исключение при выполнении запроса: {e}")
            return None
    
    def get_user_info(self):
        """Получение информации о пользователе (скоуп user:read)"""
        endpoints = [
            "core/v1/accounts/self",
            "core/v1/users/self"
        ]
        
        for endpoint in endpoints:
            result = self.get(endpoint)
            if result:
                logger.info(f"Успешное получение информации о пользователе через {endpoint}")
                return result
        
        return None
    
    def get_items_count(self, status="active"):
        """Получение количества объявлений с фильтрацией по статусу (скоуп items:info)"""
        endpoint = "core/v1/items"
        
        params = {
            "per_page": 1,
            "page": 1,
            "status": status
        }
        
        result = self.get(endpoint, params)
        if result:
            logger.info(f"Успешное получение количества объявлений через {endpoint}")
            if "meta" in result and "total" in result["meta"]:
                return result["meta"]["total"]
            elif "count" in result:
                return result["count"]
            elif "items" in result and isinstance(result["items"], list):
                return len(result["items"])
            else:
                logger.warning("Ответ не содержит ожидаемых данных для количества объявлений.")
        else:
            logger.error("Не удалось получить данные о количестве объявлений.")
        
        return 0  # Если не удалось получить данные, возвращаем 0
    
    def get_item_stats(self, item_id):
        """Получение статистики просмотров объявления"""
        endpoint = f"stats/v1/items/{item_id}"
        result = self.get(endpoint)
        return result

# Пример использования API
client_id = "kKQ5kxCxhcKoqw2oRx2V"  # Замените на ваш client_id
client_secret = "Y9C7tgtwP0uNLqoA5g5WR0GkoqkGzDJZwdroCnZ7"  # Замените на ваш client_secret

api = AvitoAPI(client_id, client_secret)

# Получаем информацию о пользователе
user_info = api.get_user_info()
if user_info:
    print("Информация о пользователе:")
    print(f"Имя: {user_info.get('name', 'неизвестно')}")
    print(f"Email: {user_info.get('email', 'неизвестно')}")
    print(f"Телефон: {user_info.get('phone', 'неизвестно')}")
    print(f"ID пользователя: {user_info.get('user_id', 'неизвестно')}")
    print(f"Дата регистрации: {user_info.get('regDate', 'неизвестно')}")
else:
    print("Не удалось получить информацию о пользователе.")

# Получаем общее количество объявлений
total_items_count = api.get_items_count()
print(f"Общее количество объявлений: {total_items_count}")

if total_items_count == 0:
    logger.warning("Количество объявлений равно нулю. Проверьте настройки аккаунта или статус объявлений.")

# Получаем список всех объявлений пользователя
endpoint = "core/v1/items"
params = {
    "per_page": 100,
    "page": 1,
    "status": "active"
}

items_result = api.get(endpoint, params)
if items_result and "items" in items_result and isinstance(items_result["items"], list):
    print("\nСписок объявлений пользователя:")
    for idx, item in enumerate(items_result["items"], 1):
        item_id = item.get('id', 'неизвестно')
        print(f"\nОбъявление #{idx}:")
        print(f"ID: {item_id}")
        print(f"Название: {item.get('title', 'неизвестно')}")
        print(f"Цена: {item.get('price', 'неизвестно')}")
        print(f"Статус: {item.get('status', 'неизвестно')}")
        print(f"Ссылка: {item.get('url', 'неизвестно')}")
        
        # Получаем статистику просмотров для каждого объявления
        stats = api.get_item_stats(item_id)
        if stats:
            print(f"Просмотры: {stats.get('views', 'неизвестно')}")
            print(f"Уникальные просмотры: {stats.get('uniqViews', 'неизвестно')}")
            if 'dailyStats' in stats:
                print("Статистика просмотров по дням:")
                for day_stat in stats['dailyStats']:
                    date = day_stat.get('date', 'неизвестно')
                    views = day_stat.get('views', 0)
                    print(f"  {date}: {views} просмотров")
        
    if "meta" in items_result and "total" in items_result["meta"]:
        total_pages = (items_result["meta"]["total"] + params["per_page"] - 1) // params["per_page"]
        if total_pages > 1:
            print(f"\nВсего страниц с объявлениями: {total_pages}. Показана страница 1.")
            
            print("\nПолучение объявлений с остальных страниц...")
            for page in range(2, total_pages + 1):
                params["page"] = page
                page_items = api.get(endpoint, params)
                if page_items and "items" in page_items and isinstance(page_items["items"], list):
                    for idx, item in enumerate(page_items["items"], 1 + (page-1)*params["per_page"]):
                        item_id = item.get('id', 'неизвестно')
                        print(f"\nОбъявление #{idx}:")
                        print(f"ID: {item_id}")
                        print(f"Название: {item.get('title', 'неизвестно')}")
                        print(f"Цена: {item.get('price', 'неизвестно')}")
                        print(f"Статус: {item.get('status', 'неизвестно')}")
                        print(f"Ссылка: {item.get('url', 'неизвестно')}")
                        
                        stats = api.get_item_stats(item_id)
                        if stats:
                            print(f"Просмотры: {stats.get('views', 'неизвестно')}")
                            print(f"Уникальные просмотры: {stats.get('uniqViews', 'неизвестно')}")
else:
    print("\nНе удалось получить список объявлений пользователя.")
