import requests
import logging
import datetime
from django.conf import settings

logger = logging.getLogger(__name__)

class AvitoApiService:
    """Сервис для работы с API Авито"""
    
    def __init__(self, client_id, client_secret):
        """Инициализация с client_id и client_secret"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://api.avito.ru"
        self.access_token = None
        self.token_expires_at = None
    
    def get_access_token(self):
        """Получение токена доступа"""
        # Проверяем, есть ли у нас актуальный токен
        now = datetime.datetime.now()
        if self.access_token and self.token_expires_at and now < self.token_expires_at:
            return self.access_token
        
        # Если токена нет или он истек, получаем новый
        token_url = f"{self.api_url}/token"
        headers = {"Content-Type": "application/x-www-form-urlencoded"}
        data = {
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret
        }
        
        try:
            response = requests.post(token_url, headers=headers, data=data)
            
            if response.status_code == 200:
                token_data = response.json()
                self.access_token = token_data.get("access_token")
                expires_in = token_data.get("expires_in", 3600)  # По умолчанию 1 час
                self.token_expires_at = now + datetime.timedelta(seconds=expires_in - 60)  # Вычитаем 60 секунд для подстраховки
                return self.access_token
            else:
                logger.error(f"Ошибка при получении токена: {response.text}")
                return None
        except Exception as e:
            logger.error(f"Исключение при получении токена: {e}")
            return None
    
    def get_user_profile(self):
        """Получение профиля пользователя"""
        token = self.get_access_token()
        if not token:
            return {"error": "Не удалось получить токен доступа"}
        
        try:
            profile_url = f"{self.api_url}/core/v1/accounts/self"
            headers = {"Authorization": f"Bearer {token}"}
            response = requests.get(profile_url, headers=headers)
            
            if response.status_code == 200:
                return response.json()
            else:
                return {"error": f"Ошибка при получении профиля: {response.text}"}
        except Exception as e:
            return {"error": f"Исключение при получении профиля: {str(e)}"}
    
    def get_daily_statistics(self):
        """Получение статистики за день"""
        token = self.get_access_token()
        if not token:
            return {"error": "Не удалось получить токен доступа"}
        
        try:
            # Здесь должна быть реализация получения дневной статистики
            # Поскольку нет соответствующего метода в API, устанавливаем заглушки
            return {
                "current": {
                    "ads_count": 0,
                    "views": 0,
                    "contacts": 0,
                    "calls": 0
                },
                "previous": {
                    "ads_count": 0,
                    "views": 0,
                    "contacts": 0,
                    "calls": 0
                }
            }
        except Exception as e:
            return {"error": f"Ошибка при получении дневной статистики: {str(e)}"}
    
    def get_weekly_statistics(self):
        """Получение статистики за неделю"""
        token = self.get_access_token()
        if not token:
            return {"error": "Не удалось получить токен доступа"}
        
        try:
            # Здесь должна быть реализация получения недельной статистики
            # Поскольку нет соответствующего метода в API, устанавливаем заглушки
            return {
                "current": {
                    "ads_count": 0,
                    "views": 0,
                    "contacts": 0,
                    "calls": 0
                },
                "previous": {
                    "ads_count": 0,
                    "views": 0,
                    "contacts": 0,
                    "calls": 0
                }
            }
        except Exception as e:
            return {"error": f"Ошибка при получении недельной статистики: {str(e)}"}
    
    def format_daily_stats(self, stats_data):
        """Форматирование дневной статистики в читаемый вид"""
        # Реализация форматирования дневной статистики
        return "Данные дневной статистики недоступны"
    
    def format_weekly_stats(self, stats_data):
        """Форматирование недельной статистики в читаемый вид"""
        # Реализация форматирования недельной статистики
        return "Данные недельной статистики недоступны"
    
    def get_account_stats(self):
        """Получение детальной информации о состоянии аккаунта"""
        token = self.get_access_token()
        if not token:
            return {"error": "Не удалось получить токен доступа"}
        
        try:
            current_stats = {}
            previous_stats = {}
            
            # Получаем информацию о балансе пользователя
            # Используем актуальный эндпоинт для получения баланса
            balance_url = f"{self.api_url}/cpa/v3/balanceInfo"
            headers = {
                "Authorization": f"Bearer {token}",
                "X-Source": "AvitoTelegramBot",
                "Content-Type": "application/json"
            }
            
            # Согласно документации, нужно передать пустой объект в теле запроса
            balance_payload = "{}"
            
            response = requests.post(balance_url, headers=headers, data=balance_payload)
            
            if response.status_code != 200:
                return {"error": f"Ошибка при получении баланса: {response.text}"}
            
            balance_data = response.json()
            logger.info(f"Получен ответ о балансе: {balance_data}")
            
            # Получаем список объявлений пользователя без ограничения на 50
            try:
                all_items = []
                page = 1
                per_page = 100  # Максимально допустимое значение для API
                
                # Получаем все страницы с объявлениями
                while True:
                    items_url = f"{self.api_url}/core/v1/items"
                    params = {
                        "per_page": per_page,
                        "page": page,
                        "status": "active"  # Только активные объявления
                    }
                    
                    items_response = requests.get(items_url, headers=headers, params=params)
                    
                    if items_response.status_code != 200:
                        logger.error(f"Ошибка при получении объявлений (страница {page}): {items_response.text}")
                        break
                    
                    items_data = items_response.json()
                    resources = items_data.get("resources", [])
                    
                    if not resources:
                        break  # Если больше нет объявлений, выходим из цикла
                    
                    all_items.extend(resources)
                    
                    # Проверяем, есть ли следующая страница
                    meta = items_data.get("meta", {})
                    if page >= meta.get("pages", 1):
                        break
                    
                    page += 1
                
                # Если получили список объявлений, сохраняем их ID для дальнейшего получения статистики
                item_ids = [item.get("id") for item in all_items if "id" in item]
                current_stats["ads_count"] = len(item_ids)
                
                # Если есть объявления, получаем их статистику
                if item_ids:
                    # Получаем статистику по объявлениям за последние 30 дней
                    today = datetime.datetime.now()
                    thirty_days_ago = today - datetime.timedelta(days=1)
                    
                    # Приведем список item_ids к нужному виду перед отправкой
                    # API позволяет отправить не более 200 ID за один запрос
                    total_views = 0
                    total_contacts = 0
                    total_favorites = 0
                    
                    # Обрабатываем ID по группам не более 200 штук
                    for i in range(0, len(item_ids), 200):
                        chunk_ids = item_ids[i:i+200]
                        
                        # Получаем статистику без использования параметра self
                        stats_headers = {
                            "Authorization": f"Bearer {token}",
                            "Content-Type": "application/json"
                        }
                        
                        # Пробуем прямой запрос к API согласно документации
                        try:
                            # Попробуем использовать основной URL для статистики
                            stats_url = f"{self.api_url}/stats/v1/accounts/self/items"
                            logger.info(f"Запрашиваем статистику объявлений с URL: {stats_url}")
                            
                            stats_payload = {
                                "dateFrom": thirty_days_ago.strftime("%Y-%m-%d"),
                                "dateTo": today.strftime("%Y-%m-%d"),
                                "fields": ["uniqViews", "uniqContacts", "uniqFavorites"],
                                "itemIds": chunk_ids,
                                "periodGrouping": "day"
                            }
                            
                            logger.info(f"Запрос статистики с payload: {stats_payload}")
                            stats_response = requests.post(stats_url, headers=stats_headers, json=stats_payload)
                            logger.info(f"Получен ответ с кодом: {stats_response.status_code}")
                            
                            if stats_response.status_code == 200:
                                stats_data = stats_response.json()
                                logger.info(f"Получен успешный ответ от API статистики: {stats_data}")
                                
                                # Данные приходят в формате, описанном в документации
                                stats_items = stats_data.get("result", {}).get("items", [])
                                
                                # Обрабатываем каждое объявление в ответе
                                for item_stat in stats_items:
                                    # Получаем массив статистики по дням для этого объявления
                                    item_stats = item_stat.get("stats", [])
                                    for day_stat in item_stats:
                                        # Суммируем статистику по каждому дню
                                        total_views += day_stat.get("uniqViews", 0)
                                        total_contacts += day_stat.get("uniqContacts", 0)
                                        total_favorites += day_stat.get("uniqFavorites", 0)
                            else:
                                # Выводим подробную информацию об ошибке
                                logger.error(f"Ошибка при получении статистики объявлений (группа {i//200+1}): {stats_response.status_code} {stats_response.text}")
                                
                                # Если получили 404, пробуем с ID пользователя
                                if stats_response.status_code == 404:
                                    logger.info("Пробуем альтернативный URL с ID пользователя")
                                    profile_data = self.get_user_profile()
                                    if "error" not in profile_data and "id" in profile_data:
                                        user_id = profile_data.get("id")
                                        alt_stats_url = f"{self.api_url}/stats/v1/accounts/{user_id}/items"
                                        logger.info(f"Повторный запрос с URL: {alt_stats_url}")
                                        
                                        alt_stats_response = requests.post(alt_stats_url, headers=stats_headers, json=stats_payload)
                                        
                                        if alt_stats_response.status_code == 200:
                                            alt_stats_data = alt_stats_response.json()
                                            logger.info(f"Успешный ответ от альтернативного URL: {alt_stats_data}")
                                            
                                            # Обрабатываем данные так же, как и в основном запросе
                                            alt_stats_items = alt_stats_data.get("result", {}).get("items", [])
                                            
                                            for item_stat in alt_stats_items:
                                                item_stats = item_stat.get("stats", [])
                                                for day_stat in item_stats:
                                                    total_views += day_stat.get("uniqViews", 0)
                                                    total_contacts += day_stat.get("uniqContacts", 0)
                                                    total_favorites += day_stat.get("uniqFavorites", 0)
                                        else:
                                            logger.error(f"Альтернативный URL также вернул ошибку: {alt_stats_response.status_code} {alt_stats_response.text}")
                        except Exception as e:
                            logger.error(f"Исключение при получении статистики объявлений: {e}")
                    
                    # Заполняем статистику
                    current_stats["views"] = total_views
                    current_stats["contacts"] = total_contacts
                    current_stats["favorites"] = total_favorites
                    
                    # Определяем значения для предыдущего периода для расчета процентов
                    # Для этого сделаем запрос за предыдущие 30 дней
                    sixty_days_ago = today - datetime.timedelta(days=60)
                    thirty_one_days_ago = today - datetime.timedelta(days=31)
                    
                    prev_total_views = 0
                    prev_total_contacts = 0
                    
                    # Обрабатываем ID по группам не более 200 штук для предыдущего периода
                    for i in range(0, len(item_ids), 200):
                        chunk_ids = item_ids[i:i+200]
                        
                        try:
                            # Используем тот же URL, что и для текущего периода
                            prev_stats_url = f"{self.api_url}/stats/v1/accounts/self/items"
                            
                            prev_stats_payload = {
                                "dateFrom": sixty_days_ago.strftime("%Y-%m-%d"),
                                "dateTo": thirty_one_days_ago.strftime("%Y-%m-%d"),
                                "fields": ["uniqViews", "uniqContacts"],
                                "itemIds": chunk_ids,
                                "periodGrouping": "day"
                            }
                            
                            prev_stats_response = requests.post(prev_stats_url, headers=stats_headers, json=prev_stats_payload)
                            
                            if prev_stats_response.status_code == 200:
                                prev_stats_data = prev_stats_response.json()
                                
                                # Обрабатываем данные в формате API
                                prev_stats_items = prev_stats_data.get("result", {}).get("items", [])
                                
                                for item_stat in prev_stats_items:
                                    item_stats = item_stat.get("stats", [])
                                    for day_stat in item_stats:
                                        prev_total_views += day_stat.get("uniqViews", 0)
                                        prev_total_contacts += day_stat.get("uniqContacts", 0)
                            else:
                                # Если получили 404, пробуем с ID пользователя, если он есть
                                if prev_stats_response.status_code == 404 and "user_id" in locals() and user_id:
                                    alt_prev_stats_url = f"{self.api_url}/stats/v1/accounts/{user_id}/items"
                                    alt_prev_stats_response = requests.post(alt_prev_stats_url, headers=stats_headers, json=prev_stats_payload)
                                    
                                    if alt_prev_stats_response.status_code == 200:
                                        alt_prev_stats_data = alt_prev_stats_response.json()
                                        alt_prev_stats_items = alt_prev_stats_data.get("result", {}).get("items", [])
                                        
                                        for item_stat in alt_prev_stats_items:
                                            item_stats = item_stat.get("stats", [])
                                            for day_stat in item_stats:
                                                prev_total_views += day_stat.get("uniqViews", 0)
                                                prev_total_contacts += day_stat.get("uniqContacts", 0)
                                    else:
                                        logger.error(f"Альтернативный URL для предыдущего периода вернул ошибку: {alt_prev_stats_response.status_code} {alt_prev_stats_response.text}")
                                else:
                                    logger.error(f"Ошибка при получении предыдущей статистики (группа {i//200+1}): {prev_stats_response.status_code} {prev_stats_response.text}")
                        except Exception as e:
                            logger.error(f"Исключение при получении предыдущей статистики: {e}")
                    
                    # Заполняем статистику за предыдущий период
                    previous_stats["views"] = prev_total_views
                    previous_stats["contacts"] = prev_total_contacts
            except Exception as e:
                logger.error(f"Ошибка при получении списка объявлений: {str(e)}")
                # Если не удалось получить список объявлений, продолжаем с тем, что есть
                pass
            
            # Получаем статистику звонков по времени создания
            calls_url = f"{self.api_url}/cpa/v2/callsByTime"
            # Текущая дата
            today = datetime.datetime.now()
            thirty_days_ago = today - datetime.timedelta(days=30)
            
            # Параметры для запроса звонков за последние 30 дней в формате RFC3339
            calls_payload = {
                "dateTimeFrom": thirty_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": 1000,  # Увеличиваем лимит для получения всех звонков за период
                "offset": 0
            }
            
            response = requests.post(calls_url, headers=headers, json=calls_payload)
            
            calls_count = 0
            if response.status_code != 200:
                calls_data = {"error": f"Ошибка при получении данных о звонках: {response.text}"}
                current_stats["calls"] = 0
            else:
                calls_data = response.json()
                # Считаем количество звонков
                calls = calls_data.get("calls", [])
                calls_count = len(calls)
                current_stats["calls"] = calls_count
                
                # Если контактов не было получено из статистики объявлений и есть данные о звонках,
                # используем эту информацию
                if "contacts" not in current_stats:
                    current_stats["contacts"] = calls_count
                # Если контакты были получены из статистики объявлений, но не учтены звонки,
                # добавляем их к общему числу контактов
                elif "contacts" in current_stats and calls_count > 0:
                    current_stats["contacts"] += calls_count
            
            # Получаем чаты за текущий период
            chats_url = f"{self.api_url}/cpa/v2/chatsByTime"
            
            # Используем те же временные рамки, что и для звонков
            chats_payload = {
                "dateTimeFrom": thirty_days_ago.strftime("%Y-%m-%dT%H:%M:%SZ"),
                "limit": 1000,  # Увеличиваем лимит для получения всех чатов за период
                "offset": 0
            }
            
            response = requests.post(chats_url, headers=headers, json=chats_payload)
            
            if response.status_code != 200:
                chats_data = {"error": f"Ошибка при получении данных о чатах: {response.text}"}
                current_stats["unanswered_messages"] = 0
                current_stats["chats"] = 0
            else:
                chats_data = response.json()
                # Считаем общее количество чатов
                chats = chats_data.get("chats", [])
                chats_count = len(chats)
                current_stats["chats"] = chats_count
                
                # Считаем количество сообщений без ответа
                unanswered_messages = 0
                for chat in chats:
                    if "chat" in chat and not chat.get("chat", {}).get("answered", True):
                        unanswered_messages += 1
                current_stats["unanswered_messages"] = unanswered_messages
                
                # Если контактов не было получено из статистики объявлений и есть данные о чатах,
                # используем эту информацию
                if "contacts" not in current_stats:
                    current_stats["contacts"] = chats_count
                # Если контакты были получены из статистики объявлений и не учтены чаты,
                # добавляем их к общему числу контактов
                elif "contacts" in current_stats and chats_count > 0:
                    current_stats["contacts"] += chats_count
            
            # Получаем данные о пропущенных звонках
            # Считаем пропущенные звонки из полученных данных
            missed_calls = 0
            if "calls" in calls_data:
                for call in calls_data.get("calls", []):
                    # Проверяем статус звонка (если есть информация о статусе)
                    if "statusId" in call and call.get("statusId") == 2:  # Предполагаем, что statusId=2 означает пропущенный звонок
                        missed_calls += 1
            current_stats["missed_calls"] = missed_calls
            
            # Если не удалось получить значения выше, используем 0
            if "ads_count" not in current_stats:
                current_stats["ads_count"] = 0
            if "views" not in current_stats:
                current_stats["views"] = 0
            if "contacts" not in current_stats:
                # Если контакты не получены ни одним способом, устанавливаем 0
                current_stats["contacts"] = 0
            
            # Заполняем предыдущие значения для расчета процентов, если они не были получены
            if "views" not in previous_stats:
                previous_stats["views"] = 0
            if "contacts" not in previous_stats:
                previous_stats["contacts"] = 0
            
            # Заполняем оставшиеся данные для сравнения
            previous_stats["ads_count"] = current_stats.get("ads_count", 0)
            previous_stats["calls"] = current_stats.get("calls", 0)
            
            # Рассчитываем уровень сервиса как процент отвеченных звонков и сообщений
            total_interactions = current_stats.get("calls", 0) + current_stats.get("chats", 0)
            missed_interactions = current_stats.get("missed_calls", 0) + current_stats.get("unanswered_messages", 0)
            
            if total_interactions > 0:
                service_level = int(((total_interactions - missed_interactions) / total_interactions) * 100)
            else:
                service_level = 0
            
            current_stats["service_level"] = service_level
            current_stats["new_reviews"] = 0  # Нет API для получения отзывов
            
            # Получаем данные о расходах
            # Расходы на продвижение объявлений
            promotion_expenses_url = f"{self.api_url}/cpa/v1/expenses/promotion"
            
            # Получаем данные за последние 30 дней
            today = datetime.datetime.now()
            thirty_days_ago = today - datetime.timedelta(days=30)
            
            promotion_payload = {
                "dateFrom": thirty_days_ago.strftime("%Y-%m-%d"),
                "dateTo": today.strftime("%Y-%m-%d")
            }
            
            # Выполняем запрос для получения расходов на продвижение
            promotion_response = requests.get(promotion_expenses_url, headers=headers, params=promotion_payload)
            
            # Инициализируем переменные для расходов
            total_expenses = 0
            promotion_expenses = 0
            xl_expenses = 0
            discounts_expenses = 0
            
            # Обрабатываем ответ API о расходах на продвижение
            if promotion_response.status_code == 200:
                promotion_data = promotion_response.json()
                logger.info(f"Получены данные о расходах на продвижение: {promotion_data}")
                
                # Извлекаем общую сумму расходов на продвижение
                promotion_expenses = promotion_data.get("total", 0) / 100  # Переводим копейки в рубли
                total_expenses += promotion_expenses
                
            else:
                logger.error(f"Ошибка при получении данных о расходах на продвижение: {promotion_response.status_code} {promotion_response.text}")
            
            # Получаем расходы на XL и выделение
            xl_expenses_url = f"{self.api_url}/cpa/v1/expenses/vas"
            
            xl_payload = {
                "dateFrom": thirty_days_ago.strftime("%Y-%m-%d"),
                "dateTo": today.strftime("%Y-%m-%d")
            }
            
            # Выполняем запрос для получения расходов на XL и выделение
            xl_response = requests.get(xl_expenses_url, headers=headers, params=xl_payload)
            
            # Обрабатываем ответ API о расходах на XL и выделение
            if xl_response.status_code == 200:
                xl_data = xl_response.json()
                logger.info(f"Получены данные о расходах на XL и выделение: {xl_data}")
                
                # Извлекаем общую сумму расходов на XL и выделение
                xl_expenses = xl_data.get("total", 0) / 100  # Переводим копейки в рубли
                total_expenses += xl_expenses
                
            else:
                logger.error(f"Ошибка при получении данных о расходах на XL и выделение: {xl_response.status_code} {xl_response.text}")
            
            # Получаем расходы на рассылку скидок
            discounts_expenses_url = f"{self.api_url}/cpa/v1/expenses/discounts"
            
            discounts_payload = {
                "dateFrom": thirty_days_ago.strftime("%Y-%m-%d"),
                "dateTo": today.strftime("%Y-%m-%d")
            }
            
            # Выполняем запрос для получения расходов на рассылку скидок
            discounts_response = requests.get(discounts_expenses_url, headers=headers, params=discounts_payload)
            
            # Обрабатываем ответ API о расходах на рассылку скидок
            if discounts_response.status_code == 200:
                discounts_data = discounts_response.json()
                logger.info(f"Получены данные о расходах на рассылку скидок: {discounts_data}")
                
                # Извлекаем общую сумму расходов на рассылку скидок
                discounts_expenses = discounts_data.get("total", 0) / 100  # Переводим копейки в рубли
                total_expenses += discounts_expenses
                
            else:
                logger.error(f"Ошибка при получении данных о расходах на рассылку скидок: {discounts_response.status_code} {discounts_response.text}")
            
            # Получаем предыдущие расходы для сравнения
            # Определяем период для предыдущих расходов
            sixty_days_ago = today - datetime.timedelta(days=60)
            thirty_one_days_ago = today - datetime.timedelta(days=31)
            
            prev_promotion_payload = {
                "dateFrom": sixty_days_ago.strftime("%Y-%m-%d"),
                "dateTo": thirty_one_days_ago.strftime("%Y-%m-%d")
            }
            
            # Запрашиваем предыдущие расходы на продвижение
            prev_promotion_response = requests.get(promotion_expenses_url, headers=headers, params=prev_promotion_payload)
            prev_promotion_expenses = 0
            
            if prev_promotion_response.status_code == 200:
                prev_promotion_data = prev_promotion_response.json()
                prev_promotion_expenses = prev_promotion_data.get("total", 0) / 100
            else:
                logger.error(f"Ошибка при получении предыдущих данных о расходах на продвижение: {prev_promotion_response.status_code} {prev_promotion_response.text}")
            
            # Запрашиваем предыдущие расходы на XL и выделение
            prev_xl_response = requests.get(xl_expenses_url, headers=headers, params=prev_promotion_payload)
            prev_xl_expenses = 0
            
            if prev_xl_response.status_code == 200:
                prev_xl_data = prev_xl_response.json()
                prev_xl_expenses = prev_xl_data.get("total", 0) / 100
            else:
                logger.error(f"Ошибка при получении предыдущих данных о расходах на XL и выделение: {prev_xl_response.status_code} {prev_xl_response.text}")
            
            # Запрашиваем предыдущие расходы на рассылку скидок
            prev_discounts_response = requests.get(discounts_expenses_url, headers=headers, params=prev_promotion_payload)
            prev_discounts_expenses = 0
            
            if prev_discounts_response.status_code == 200:
                prev_discounts_data = prev_discounts_response.json()
                prev_discounts_expenses = prev_discounts_data.get("total", 0) / 100
            else:
                logger.error(f"Ошибка при получении предыдущих данных о расходах на рассылку скидок: {prev_discounts_response.status_code} {prev_discounts_response.text}")
            
            # Вычисляем общие предыдущие расходы
            prev_total_expenses = prev_promotion_expenses + prev_xl_expenses + prev_discounts_expenses
            
            # Заполняем статистику текущих расходов
            current_stats["total_expenses"] = total_expenses
            current_stats["promotion_expenses"] = promotion_expenses
            current_stats["xl_expenses"] = xl_expenses
            current_stats["discounts_expenses"] = discounts_expenses
            
            # Заполняем статистику предыдущих расходов
            previous_stats["total_expenses"] = prev_total_expenses
            previous_stats["promotion_expenses"] = prev_promotion_expenses
            previous_stats["xl_expenses"] = prev_xl_expenses
            previous_stats["discounts_expenses"] = prev_discounts_expenses
            
            # Получаем значение баланса в рублях (делим на 100, т.к. значение в копейках)
            wallet_balance = balance_data.get("balance", 0) / 100 if "balance" in balance_data else 0
            
            # Собираем все данные в один словарь
            return {
                "current": current_stats,
                "previous": previous_stats,
                "balance": {
                    "cpa": 0,  # В текущем API нет разделения на CPA и кошелек
                    "wallet": wallet_balance
                },
                "managers": {
                    "missed_calls": current_stats.get("missed_calls", 0),
                    "unanswered_messages": current_stats.get("unanswered_messages", 0),
                    "service_level": current_stats.get("service_level", 0),
                    "new_reviews": current_stats.get("new_reviews", 0)
                },
                "expenses": {
                    "total": current_stats.get("total_expenses", 0),
                    "promotion": current_stats.get("promotion_expenses", 0),
                    "xl": current_stats.get("xl_expenses", 0),
                    "discounts": current_stats.get("discounts_expenses", 0)
                }
            }
            
        except Exception as e:
            return {"error": f"Ошибка при получении данных о состоянии аккаунта: {str(e)}"}
    
    def format_account_stats(self, stats_data):
        """Форматирование данных о состоянии аккаунта в читаемый вид"""
        # Если есть ошибка, вернем сообщение об ошибке
        if "error" in stats_data:
            return f"⚠️ Ошибка при получении данных: {stats_data['error']}"
        
        # Получаем текущую дату для отчета
        today = datetime.datetime.now().strftime("%d.%m.%Y")
        
        # Формируем заголовок отчета
        report = f"📊 Отчет за {today}\n\n"
        
        # Показатели
        report += "📈 Показатели\n"
        
        # Если есть данные о статистике объявлений
        if "current" in stats_data and "previous" in stats_data:
            current_stats = stats_data["current"]
            previous_stats = stats_data["previous"]
            
            # Объявления
            ads_count = current_stats.get("ads_count", 0)
            prev_ads_count = previous_stats.get("ads_count", 0)
            ads_percent = self._calculate_percent_change(ads_count, prev_ads_count)
            report += f"✔️Объявления: {ads_count} шт ({ads_percent}%)\n"
            
            # Просмотры
            views = current_stats.get("views", 0)
            prev_views = previous_stats.get("views", 0)
            views_percent = self._calculate_percent_change(views, prev_views)
            report += f"✔️Просмотры: {views} ({views_percent}%)\n"
            
            # Контакты
            contacts = current_stats.get("contacts", 0)
            prev_contacts = previous_stats.get("contacts", 0)
            contacts_percent = self._calculate_percent_change(contacts, prev_contacts)
            report += f"✔️Контакты: {contacts} ({contacts_percent}%)\n"
            
            # Конверсия в контакты
            conversion = (contacts / views * 100) if views > 0 else 0
            prev_conversion = (prev_contacts / prev_views * 100) if prev_views > 0 else 0
            conversion_percent = self._calculate_percent_change(conversion, prev_conversion)
            report += f"✔️Конверсия в контакты: {conversion:.1f}% ({conversion_percent}%)\n"
            
            # Стоимость контакта
            expenses = stats_data.get("expenses", {})
            total_expenses = expenses.get("total", 0)
            cost_per_contact = total_expenses / contacts if contacts > 0 else 0
            prev_total_expenses = previous_stats.get("total_expenses", 0)
            prev_cost_per_contact = prev_total_expenses / prev_contacts if prev_contacts > 0 else 0
            cost_percent = self._calculate_percent_change(cost_per_contact, prev_cost_per_contact)
            report += f"✔️Стоимость контакта: {cost_per_contact:.0f} ₽ ({cost_percent}%)\n"
            
            # Звонки
            calls = current_stats.get("calls", 0)
            prev_calls = previous_stats.get("calls", 0)
            calls_percent = self._calculate_percent_change(calls, prev_calls)
            report += f"❗️Всего звонков: {calls} ({calls_percent}%)\n"
        
        # Расходы
        expenses = stats_data.get("expenses", {})
        if expenses:
            report += "\n💰 Расходы\n"
            
            # Общие расходы
            total = expenses.get("total", 0)
            prev_total = previous_stats.get("total_expenses", 0)
            total_percent = self._calculate_percent_change(total, prev_total)
            report += f"Общие: {total} ₽ ({total_percent}%)\n"
            
            # Расходы на продвижение
            promotion = expenses.get("promotion", 0)
            prev_promotion = previous_stats.get("promotion_expenses", 0)
            promotion_percent = self._calculate_percent_change(promotion, prev_promotion)
            report += f"На продвижение: {promotion} ₽ ({promotion_percent}%)\n"
            
            # Расходы на XL и выделение
            xl = expenses.get("xl", 0)
            prev_xl = previous_stats.get("xl_expenses", 0)
            xl_percent = self._calculate_percent_change(xl, prev_xl)
            report += f"На XL и выделение: {xl} ₽ ({xl_percent}%)\n"
            
            # Рассылка скидок
            discounts = expenses.get("discounts", 0)
            prev_discounts = previous_stats.get("discounts_expenses", 0)
            discounts_percent = self._calculate_percent_change(discounts, prev_discounts)
            report += f"Рассылка скидок: {discounts} ₽ ({discounts_percent}%)\n"
        
        # Работа менеджеров
        managers = stats_data.get("managers", {})
        if managers:
            report += "\n👥 Работа менеджеров\n"
            
            # Непринятые звонки
            missed_calls = managers.get("missed_calls", 0)
            report += f"Непринятые звонки: {missed_calls}\n"
            
            # Сообщения без ответа
            unanswered_messages = managers.get("unanswered_messages", 0)
            report += f"Сообщения без ответа: {unanswered_messages}\n"
            
            # Уровень сервиса
            service_level = managers.get("service_level", 0)
            report += f"Уровень сервиса: {service_level}%\n"
            
            # Новые отзывы
            new_reviews = managers.get("new_reviews", 0)
            report += f"Новые отзывы: {new_reviews}\n"
        
        # Баланс
        balance = stats_data.get("balance", {})
        if balance:
            report += "\n—————————\n"
            
            # CPA баланс
            cpa_balance = balance.get("cpa", 0)
            report += f"CPA баланс: {cpa_balance} ₽\n"
            
            # Кошелек
            wallet = balance.get("wallet", 0)
            report += f"Кошелек: {wallet} ₽"
        
        return report
    
    def _calculate_percent_change(self, current, previous):
        """Расчет процентного изменения между текущим и предыдущим значением"""
        if previous == 0:
            return 0.0
        
        change = ((current - previous) / previous) * 100
        return round(change, 1) 