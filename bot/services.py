import requests
import logging
import datetime
from django.conf import settings
from bot.models import User, UserBalance
from django.db.models import Q
from decimal import Decimal

logger = logging.getLogger(__name__)

class AvitoApiService:
    """Сервис для работы с API Авито"""
    
    def __init__(self, client_id, client_secret, user=None):
        """Инициализация с client_id, client_secret и объектом пользователя"""
        self.client_id = client_id
        self.client_secret = client_secret
        self.api_url = "https://api.avito.ru"
        self.access_token = None
        self.token_expires_at = None
        self.user = user  # Добавляем пользователя, чтобы иметь доступ к его данным
    
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
            
            # Получаем значение текущего баланса в рублях (делим на 100, т.к. значение в копейках)
            current_wallet_balance = balance_data.get("balance", 0) / 100 if "balance" in balance_data else 0
            
            # Если есть привязанный пользователь, обновляем его баланс и историю
            if self.user:
                # Обновляем или создаем запись баланса на текущий день
                today = datetime.date.today()
                balance_record, created = UserBalance.objects.update_or_create(
                    user=self.user,
                    date=today,
                    defaults={'amount': Decimal(str(current_wallet_balance))}
                )
                
                # Получаем баланс за предыдущий день
                yesterday = today - datetime.timedelta(days=1)
                previous_balance_record = UserBalance.objects.filter(
                    user=self.user,
                    date=yesterday
                ).first()
                
                # Если есть запись за вчерашний день, рассчитываем расходы и пополнения
                if previous_balance_record:
                    previous_wallet_balance = float(previous_balance_record.amount)
                    
                    # Если текущий баланс больше предыдущего, было пополнение
                    if current_wallet_balance > previous_wallet_balance:
                        daily_deposit = current_wallet_balance - previous_wallet_balance
                        daily_expenses = 0
                    else:
                        # Иначе были расходы
                        daily_expenses = previous_wallet_balance - current_wallet_balance
                        daily_deposit = 0
                else:
                    # Если нет записи за предыдущий день, используем прямой запрос к API
                    previous_wallet_balance = self.get_previous_wallet_balance()
                    
                    # Если предыдущий баланс был получен успешно, рассчитываем изменения
                    if previous_wallet_balance > 0:
                        if current_wallet_balance > previous_wallet_balance:
                            daily_deposit = current_wallet_balance - previous_wallet_balance
                            daily_expenses = 0
                        else:
                            daily_expenses = previous_wallet_balance - current_wallet_balance
                            daily_deposit = 0
                    else:
                        # Если не удалось получить предыдущий баланс, устанавливаем значения в 0
                        daily_expenses = 0
                        daily_deposit = 0
            else:
                # Если нет привязанного пользователя, используем прямой запрос к API
                previous_wallet_balance = self.get_previous_wallet_balance()
                
                # Если текущий баланс больше предыдущего, было пополнение
                if current_wallet_balance > previous_wallet_balance:
                    daily_deposit = current_wallet_balance - previous_wallet_balance
                    daily_expenses = 0
                else:
                    # Иначе были расходы
                    daily_expenses = previous_wallet_balance - current_wallet_balance
                    daily_deposit = 0
            
            # Заполняем статистику текущих расходов и пополнений
            current_stats["total_expenses"] = daily_expenses
            current_stats["total_deposit"] = daily_deposit
            
            # Заполняем статистику предыдущих расходов (в данном случае это будет 0, 
            # так как мы не отслеживаем расходы за позавчера)
            previous_stats["total_expenses"] = 0
            previous_stats["total_deposit"] = 0
            
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
                    # Получаем статистику по объявлениям за текущий день
                    today = datetime.datetime.now()
                    yesterday = today - datetime.timedelta(days=1)
                    day_before_yesterday = today - datetime.timedelta(days=2)
                    
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
                                "dateFrom": yesterday.strftime("%Y-%m-%d"),
                                "dateTo": today.strftime("%Y-%m-%d"),
                                "fields": ["uniqViews", "uniqContacts", "uniqFavorites"],
                                "itemIds": chunk_ids,
                                "periodGrouping": "day"
                            }
                            
                            logger.info(f"Запрос статистики с payload: {stats_payload}")
                            stats_response = requests.post(stats_url, headers=stats_headers, json=stats_payload)
                            logger.info(f"Получен ответ с кодом: {stats_response.status_code}")
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
                    
                    # Определяем значения для предыдущего периода (позавчера) для расчета процентов
                    prev_total_views = 0
                    prev_total_contacts = 0
                    
                    # Обрабатываем ID для предыдущего дня
                    for i in range(0, len(item_ids), 200):
                        chunk_ids = item_ids[i:i+200]
                        
                        try:
                            # Используем тот же URL, что и для текущего периода
                            prev_stats_url = f"{self.api_url}/stats/v1/accounts/self/items"
                            
                            prev_stats_payload = {
                                "dateFrom": day_before_yesterday.strftime("%Y-%m-%d"),
                                "dateTo": yesterday.strftime("%Y-%m-%d"),
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
            
            # Получаем статистику звонков за текущий день
            calls_url = f"{self.api_url}/cpa/v2/callsByTime"
            # Текущая дата
            today = datetime.datetime.now()
            yesterday = today - datetime.timedelta(days=1)
            
            # Параметры для запроса звонков за вчерашний день в формате RFC3339
            calls_payload = {
                "dateTimeFrom": yesterday.strftime("%Y-%m-%dT00:00:00Z"),
                "dateTimeTo": today.strftime("%Y-%m-%dT00:00:00Z"),
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
            
            # Получаем чаты за текущий день
            chats_url = f"{self.api_url}/cpa/v2/chatsByTime"
            
            # Используем те же временные рамки, что и для звонков
            chats_payload = {
                "dateTimeFrom": yesterday.strftime("%Y-%m-%dT00:00:00Z"),
                "dateTimeTo": today.strftime("%Y-%m-%dT00:00:00Z"),
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
            
            # Собираем все данные в один словарь
            return {
                "current": current_stats,
                "previous": previous_stats,
                "balance": {
                    "cpa": 0,  # В текущем API нет разделения на CPA и кошелек
                    "wallet": current_wallet_balance,
                    "previous_wallet": previous_wallet_balance
                },
                "managers": {
                    "missed_calls": current_stats.get("missed_calls", 0),
                    "unanswered_messages": current_stats.get("unanswered_messages", 0),
                    "service_level": current_stats.get("service_level", 0),
                    "new_reviews": current_stats.get("new_reviews", 0)
                },
                "expenses": {
                    "total": daily_expenses
                },
                "deposit": {
                    "total": daily_deposit
                }
            }
            
        except Exception as e:
            return {"error": f"Ошибка при получении данных о состоянии аккаунта: {str(e)}"}
    
    def get_previous_wallet_balance(self):
        """Получение баланса кошелька за предыдущий день"""
        # Сначала пробуем получить баланс из БД, если есть привязанный пользователь
        if self.user:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            prev_balance = UserBalance.objects.filter(user=self.user, date=yesterday).first()
            if prev_balance:
                return float(prev_balance.amount)
        
        # Если не получилось, используем API (используется как запасной вариант)
        token = self.get_access_token()
        if not token:
            logger.error("Не удалось получить токен доступа для получения баланса за предыдущий день")
            return 0
        
        try:
            # Получаем информацию о балансе пользователя за вчерашний день
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
                logger.error(f"Ошибка при получении баланса за предыдущий день: {response.text}")
                return 0
            
            balance_data = response.json()
            logger.info(f"Получен ответ о балансе за предыдущий день: {balance_data}")
            
            # Получаем значение баланса в рублях (делим на 100, т.к. значение в копейках)
            previous_wallet_balance = balance_data.get("balance", 0) / 100 if "balance" in balance_data else 0
            return previous_wallet_balance
        except Exception as e:
            logger.error(f"Ошибка при получении баланса за предыдущий день: {str(e)}")
            return 0
        

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
        current_stats = stats_data.get("current", {}) or {}
        previous_stats = stats_data.get("previous", {}) or {}
        
        # Проверяем, есть ли какие-то полезные данные для отображения
        has_stats_data = any([
            current_stats.get("ads_count", 0) > 0,
            current_stats.get("views", 0) > 0,
            current_stats.get("contacts", 0) > 0,
            current_stats.get("calls", 0) > 0
        ])
        
        if has_stats_data:
            report += "📈 Показатели\n"
            
            # Объявления
            ads_count = current_stats.get("ads_count", 0) or 0
            prev_ads_count = previous_stats.get("ads_count", 0) or 0
            ads_percent = self._calculate_percent_change(ads_count, prev_ads_count)
            report += f"✔️Объявления: {ads_count} шт ({ads_percent}%)\n"
            
            # Просмотры
            views = current_stats.get("views", 0) or 0
            prev_views = previous_stats.get("views", 0) or 0
            views_percent = self._calculate_percent_change(views, prev_views)
            report += f"✔️Просмотры: {views} ({views_percent}%)\n"
            
            # Контакты
            contacts = current_stats.get("contacts", 0) or 0
            prev_contacts = previous_stats.get("contacts", 0) or 0
            contacts_percent = self._calculate_percent_change(contacts, prev_contacts)
            report += f"✔️Контакты: {contacts} ({contacts_percent}%)\n"
            
            # Конверсия в контакты
            conversion = (contacts / views * 100) if views and views > 0 else 0
            prev_conversion = (prev_contacts / prev_views * 100) if prev_views and prev_views > 0 else 0
            conversion_percent = self._calculate_percent_change(conversion, prev_conversion)
            report += f"✔️Конверсия в контакты: {conversion:.1f}% ({conversion_percent}%)\n"
            
            # Стоимость контакта
            expenses = stats_data.get("expenses", {}) or {}
            total_expenses = expenses.get("total", 0) or 0
            # Проверяем наличие контактов перед делением
            if contacts and contacts > 0 and total_expenses > 0:
                cost_per_contact = total_expenses / contacts
            else:
                cost_per_contact = 0
                
            # Проверяем предыдущие значения
            prev_total_expenses = previous_stats.get("total_expenses", 0) or 0
            if prev_contacts and prev_contacts > 0 and prev_total_expenses > 0:
                prev_cost_per_contact = prev_total_expenses / prev_contacts
            else:
                prev_cost_per_contact = 0
                
            cost_percent = self._calculate_percent_change(cost_per_contact, prev_cost_per_contact)
            report += f"✔️Стоимость контакта: {cost_per_contact:.0f} ₽ ({cost_percent}%)\n"
            
            # Звонки
            calls = current_stats.get("calls", 0) or 0
            prev_calls = previous_stats.get("calls", 0) or 0
            calls_percent = self._calculate_percent_change(calls, prev_calls)
            report += f"❗️Всего звонков: {calls} ({calls_percent}%)\n"
        else:
            report += "📈 Показатели: нет данных\n"
        
        # Расходы и пополнения
        expenses = stats_data.get("expenses", {}) or {}
        deposit = stats_data.get("deposit", {}) or {}
        
        # Добавляем заголовок "Финансы" только если действительно есть что отображать
        total_expenses = expenses.get("total", 0) or 0
        total_deposit = deposit.get("total", 0) or 0
        
        if total_expenses > 0 or total_deposit > 0:
            report += "\n💰 Финансы\n"
            
            # Проверяем, были ли расходы
            if total_expenses > 0:
                prev_total_expenses = previous_stats.get("total_expenses", 0) or 0
                total_percent = self._calculate_percent_change(total_expenses, prev_total_expenses)
                report += f"📉 Расходы: {total_expenses:.0f} ₽ ({total_percent}%)\n"
            
            # Проверяем, были ли пополнения
            if total_deposit > 0:
                prev_total_deposit = previous_stats.get("total_deposit", 0) or 0
                deposit_percent = self._calculate_percent_change(total_deposit, prev_total_deposit)
                report += f"📈 Пополнения: {total_deposit:.0f} ₽ ({deposit_percent}%)\n"
        
        # Работа менеджеров
        managers = stats_data.get("managers", {}) or {}
        
        # Проверяем, есть ли данные по работе менеджеров
        missed_calls = managers.get("missed_calls", 0) or 0
        unanswered_messages = managers.get("unanswered_messages", 0) or 0
        service_level = managers.get("service_level", 0) or 0
        new_reviews = managers.get("new_reviews", 0) or 0
        
        has_manager_data = missed_calls > 0 or unanswered_messages > 0 or service_level > 0 or new_reviews > 0
        
        if has_manager_data:
            report += "\n👥 Работа менеджеров\n"
            report += f"Непринятые звонки: {missed_calls}\n"
            report += f"Сообщения без ответа: {unanswered_messages}\n"
            report += f"Уровень сервиса: {service_level}%\n"
            report += f"Новые отзывы: {new_reviews}\n"
        
        # Баланс
        balance = stats_data.get("balance", {}) or {}
        wallet = balance.get("wallet", 0) or 0
        prev_wallet = balance.get("previous_wallet", 0) or 0
        
        if wallet > 0 or prev_wallet > 0:
            report += "\n—————————\n"
            
            # CPA баланс
            cpa_balance = balance.get("cpa", 0) or 0
            if cpa_balance > 0:
                report += f"CPA баланс: {cpa_balance} ₽\n"
            
            # Текущий баланс
            report += f"Текущий баланс: {wallet:.0f} ₽\n"
            
            # Баланс вчера
            report += f"Баланс вчера: {prev_wallet:.0f} ₽"
        
        return report
    
    def _calculate_percent_change(self, current, previous):
        """Расчет процентного изменения между текущим и предыдущим значением"""
        # Проверка на None и конвертация в числовой тип
        current = float(current or 0)
        previous = float(previous or 0)
        
        # Если оба значения равны нулю, изменения нет
        if current == 0 and previous == 0:
            return 0.0
            
        # Если предыдущее значение равно нулю, а текущее нет,
        # считаем рост как 100% (или другое значение по выбору)
        if previous == 0:
            return 100.0 if current > 0 else 0.0
        
        change = ((current - previous) / previous) * 100
        return round(change, 1) 