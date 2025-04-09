import requests
import logging
from datetime import datetime, timedelta
from bot.models import User

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
        # Проверяем, не истек ли токен
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
            
            # Устанавливаем время истечения токена (обычно 24 часа)
            expires_in = token_data.get('expires_in', 86400)  # По умолчанию 24 часа
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in)
            
            if self.token:
                logger.info(f"Токен успешно получен, действителен до {self.token_expires_at}")
            else:
                logger.error(f"Токен не найден в ответе: {token_data}")
            return self.token
        except Exception as e:
            logger.error(f"Исключение при получении токена: {e}")
            return None
    
    def _make_request(self, method, endpoint, params=None, data=None, timeout=10):
        """Выполнение запроса к API с таймаутом и обновлением токена при необходимости"""
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
        logger.info(f"Запрос к {url} методом {method}")
        
        try:
            if method.upper() == 'GET':
                response = requests.get(url, headers=headers, params=params, timeout=timeout)
            elif method.upper() == 'POST':
                response = requests.post(url, headers=headers, json=data, timeout=timeout)
            else:
                logger.error(f"Неподдерживаемый метод: {method}")
                return None
                
            logger.info(f"Ответ: {response.status_code}")
            
            if response.status_code == 401:
                # Токен истек, повторно получаем
                logger.info("Токен устарел, получаем новый")
                self.token = None
                self.token_expires_at = None
                if not self.get_token():
                    return None
                return self._make_request(method, endpoint, params, data)
                
            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"Ошибка API: {response.status_code}, {response.text}")
                return None
                
        except Exception as e:
            logger.error(f"Ошибка запроса: {e}")
            return None
    
    def get(self, endpoint, params=None):
        """GET-запрос к API"""
        return self._make_request('GET', endpoint, params=params)
    
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
        # Используем только рабочий эндпоинт, удаляем неработающий
        endpoint = "core/v1/items"
        
        params = {
            "per_page": 1,  # Запрашиваем только одно объявление для скорости
            "page": 1,
            "status": status
        }
        
        result = self.get(endpoint, params)
        if result:
            logger.info(f"Успешное получение количества объявлений через {endpoint}")
            # Возвращаем только общее количество объявлений
            if "meta" in result and "total" in result["meta"]:
                return result["meta"]["total"]
            # Для случая, если ответ не содержит meta.total
            elif "count" in result:
                return result["count"]
            elif "items" in result and isinstance(result["items"], list):
                return len(result["items"])
        
        return 0  # Если не удалось получить данные, возвращаем 0


def get_account_info(telegram_id):
    """Получение информации о пользователе и количестве объявлений"""
    try:
        user = User.objects.get(telegram_id=telegram_id)
        logger.info(f"Получение информации для пользователя {telegram_id}")
        
        if not user.avito_client_id or not user.avito_client_secret:
            return "Ошибка: Не заданы client_id и client_secret для API Авито"
        
        # Создаем экземпляр API
        api = AvitoAPI(user.avito_client_id, user.avito_client_secret)
        
        # Получаем информацию о пользователе
        user_info = api.get_user_info()
        if not user_info:
            return "Ошибка: Не удалось подключиться к API Авито. Проверьте правильность client_id и client_secret."
        
        # Получаем количество активных объявлений
        active_count = api.get_items_count(status="active")
        
        # Формируем информацию
        report = "Информация об аккаунте Авито\n\n"
        
        username = user_info.get('name', 'неизвестно')
        report += f"Имя: {username}\n"
        
        if 'email' in user_info:
            report += f"Email: {user_info.get('email')}\n"
            
        if 'phone' in user_info:
            report += f"Телефон: {user_info.get('phone')}\n"
            
        if 'user_id' in user_info:  # Изменено с 'id' на 'user_id'
            report += f"ID пользователя: {user_info.get('user_id')}\n"
        
        if 'regDate' in user_info:
            report += f"Дата регистрации: {user_info.get('regDate')}\n"
            
        report += f"\nКоличество активных объявлений: {active_count}\n"
        
        # Информация о рейтинге
        if "rating" in user_info:
            report += f"\nРейтинг: {user_info.get('rating')}\n"
            
        if "reviewsCount" in user_info:
            report += f"Количество отзывов: {user_info.get('reviewsCount')}\n"
            
        return report
        
    except User.DoesNotExist:
        return "Ошибка: Пользователь не найден"
    except Exception as e:
        logger.exception(f"Ошибка при получении информации: {e}")
        return f"Ошибка: {str(e)}"


# Функция для обратной совместимости
def get_daily_views(telegram_id):
    """Обертка для совместимости с существующим кодом"""
    return get_account_info(telegram_id) 