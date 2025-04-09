import requests
from datetime import datetime, timedelta
import logging
import json

logger = logging.getLogger(__name__)

class AvitoApiService:
    BASE_URL = "https://api.avito.ru"
    AUTH_URL = "https://api.avito.ru/oauth2/token"
    
    def __init__(self, client_id, client_secret):
        self.client_id = client_id
        self.client_secret = client_secret
        self.access_token = None
        self.token_expires_at = None
        self.headers = {
            "Content-Type": "application/json"
        }
    
    def get_access_token(self):
        """Получает токен доступа с использованием client_id и client_secret"""
        if self.access_token and self.token_expires_at and datetime.now() < self.token_expires_at:
            return self.access_token
            
        try:
            data = {
                "grant_type": "client_credentials",
                "client_id": self.client_id,
                "client_secret": self.client_secret
            }
            
            response = requests.post(
                self.AUTH_URL,
                json=data,
                headers={"Content-Type": "application/json"}
            )
            response.raise_for_status()
            token_data = response.json()
            
            self.access_token = token_data.get("access_token")
            expires_in = token_data.get("expires_in", 3600)  # По умолчанию 1 час
            self.token_expires_at = datetime.now() + timedelta(seconds=expires_in - 300)  # Минус 5 минут для запаса
            
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            
            return self.access_token
        except Exception as e:
            logger.error(f"Ошибка при получении токена доступа: {e}")
            return None
    
    def make_request(self, method, endpoint, params=None, data=None):
        """Выполняет запрос к API с автоматическим обновлением токена"""
        if not self.get_access_token():
            return {"error": "Не удалось получить токен доступа"}
        
        try:
            url = f"{self.BASE_URL}/{endpoint}"
            
            if method.lower() == "get":
                response = requests.get(url, headers=self.headers, params=params)
            elif method.lower() == "post":
                response = requests.post(url, headers=self.headers, json=data)
            else:
                return {"error": f"Неподдерживаемый метод: {method}"}
                
            response.raise_for_status()
            return response.json()
        except Exception as e:
            logger.error(f"Ошибка запроса к {endpoint}: {e}")
            return {"error": str(e)}
    
    def get_user_profile(self):
        """Получает информацию о профиле пользователя"""
        return self.make_request("get", "buyer/v1/accounts/self")
    
    def get_account_stats(self, date_from, date_to, period="day"):
        """Получает статистику аккаунта за указанный период"""
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "period": period,
            "fields": "views,uniqViews,contacts,favorites,calls"
        }
        return self.make_request("get", "stats/v1/accounts/stats", params=params)
    
    def get_items_list(self):
        """Получает список объявлений пользователя"""
        return self.make_request("get", "items/v2/get")
    
    def get_items_stats(self, date_from, date_to, period="day"):
        """Получает статистику объявлений за указанный период"""
        params = {
            "dateFrom": date_from,
            "dateTo": date_to,
            "period": period
        }
        return self.make_request("get", "stats/v1/items", params=params)
    
    def get_billing_balance(self):
        """Получает данные о балансе"""
        return self.make_request("get", "billing/v1/accounts/balance")
    
    def get_billing_transactions(self, date_from, date_to):
        """Получает данные о транзакциях"""
        params = {
            "dateFrom": date_from,
            "dateTo": date_to
        }
        return self.make_request("get", "billing/v1/accounts/transactions", params=params)
    
    def get_autoload_stats(self, date_from, date_to):
        """Получает статистику по автозагрузке"""
        params = {
            "dateFrom": date_from,
            "dateTo": date_to
        }
        return self.make_request("get", "autoload/v1/stats", params=params)
    
    def get_daily_statistics(self):
        """Получает статистику аккаунта за текущий день"""
        today = datetime.now().strftime("%Y-%m-%d")
        yesterday = (datetime.now() - timedelta(days=1)).strftime("%Y-%m-%d")
        
        # Собираем все необходимые данные с использованием правильных эндпоинтов
        account_stats = self.get_account_stats(today, today)
        prev_account_stats = self.get_account_stats(yesterday, yesterday)
        items_stats = self.get_items_stats(today, today)
        prev_items_stats = self.get_items_stats(yesterday, yesterday)
        balance_data = self.get_billing_balance()
        transactions_data = self.get_billing_transactions(today, today)
        prev_transactions_data = self.get_billing_transactions(yesterday, yesterday)
        items_list = self.get_items_list()
        
        # Формируем агрегированный результат
        return {
            "current": {
                "account_stats": account_stats,
                "items_stats": items_stats,
                "items_list": items_list,
                "balance_data": balance_data,
                "transactions_data": transactions_data
            },
            "previous": {
                "account_stats": prev_account_stats,
                "items_stats": prev_items_stats,
                "transactions_data": prev_transactions_data
            }
        }
    
    def get_weekly_statistics(self):
        """Получает статистику аккаунта за последнюю неделю"""
        today = datetime.now().strftime("%Y-%m-%d")
        week_ago = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        prev_week_start = (datetime.now() - timedelta(days=14)).strftime("%Y-%m-%d")
        prev_week_end = (datetime.now() - timedelta(days=8)).strftime("%Y-%m-%d")
        
        # Собираем все необходимые данные с использованием правильных эндпоинтов
        account_stats = self.get_account_stats(week_ago, today, period="week")
        prev_account_stats = self.get_account_stats(prev_week_start, prev_week_end, period="week")
        items_stats = self.get_items_stats(week_ago, today, period="week")
        prev_items_stats = self.get_items_stats(prev_week_start, prev_week_end, period="week")
        balance_data = self.get_billing_balance()
        transactions_data = self.get_billing_transactions(week_ago, today)
        prev_transactions_data = self.get_billing_transactions(prev_week_start, prev_week_end)
        items_list = self.get_items_list()
        
        # Формируем агрегированный результат
        return {
            "current": {
                "account_stats": account_stats,
                "items_stats": items_stats,
                "items_list": items_list,
                "balance_data": balance_data,
                "transactions_data": transactions_data
            },
            "previous": {
                "account_stats": prev_account_stats,
                "items_stats": prev_items_stats,
                "transactions_data": prev_transactions_data
            }
        }
    
    def format_daily_stats(self, stats):
        """Форматирует ежедневную статистику для вывода"""
        if "error" in stats:
            return f"Ошибка при получении статистики: {stats['error']}"
        
        try:
            today = datetime.now().strftime("%d.%m.%Y")
            
            # Извлекаем данные из ответа API
            current_data = stats["current"]
            previous_data = stats["previous"]
            
            # Данные статистики аккаунта
            account_stats = self._safe_get_results(current_data, "account_stats", "result")
            prev_account_stats = self._safe_get_results(previous_data, "account_stats", "result")
            
            # Данные статистики объявлений
            items_stats = self._safe_get_results(current_data, "items_stats", "result")
            prev_items_stats = self._safe_get_results(previous_data, "items_stats", "result")
            
            # Данные о списке объявлений
            items_list = current_data.get("items_list", {})
            ads_count = len(self._safe_get_results(current_data, "items_list", "items"))
            
            # Данные о балансе
            balance_data = current_data.get("balance_data", {})
            
            # Данные о транзакциях
            transactions_data = self._safe_get_results(current_data, "transactions_data", "result")
            prev_transactions_data = self._safe_get_results(previous_data, "transactions_data", "result")
            
            # Извлекаем метрики из статистики аккаунта
            current_day_stats = self._get_latest_day_stats(account_stats)
            prev_day_stats = self._get_latest_day_stats(prev_account_stats)
            
            # Количество объявлений и процент изменения
            prev_ads_count = self._extract_value(items_stats, "totalCount", 0)
            ads_percent = self._calculate_percentage_change(prev_ads_count, ads_count)
            
            # Просмотры
            views = self._extract_value(current_day_stats, "views", 0)
            prev_views = self._extract_value(prev_day_stats, "views", 0)
            views_percent = self._calculate_percentage_change(prev_views, views)
            
            # Контакты
            contacts = self._extract_value(current_day_stats, "contacts", 0)
            prev_contacts = self._extract_value(prev_day_stats, "contacts", 0)
            contacts_percent = self._calculate_percentage_change(prev_contacts, contacts)
            
            # Звонки
            calls = self._extract_value(current_day_stats, "calls", 0)
            prev_calls = self._extract_value(prev_day_stats, "calls", 0)
            calls_percent = self._calculate_percentage_change(prev_calls, calls)
            
            # Конверсия в контакты (из просмотров)
            conversion = round((contacts / views * 100) if views > 0 else 0, 1)
            prev_conversion = round((prev_contacts / prev_views * 100) if prev_views > 0 else 0, 1)
            conversion_percent = self._calculate_percentage_change(prev_conversion, conversion)
            
            # Расходы
            total_expenses = self._calculate_total_expenses(transactions_data)
            prev_total_expenses = self._calculate_total_expenses(prev_transactions_data)
            expenses_percent = self._calculate_percentage_change(prev_total_expenses, total_expenses)
            
            # Стоимость контакта
            contact_cost = round(total_expenses / contacts if contacts > 0 else 0)
            prev_contact_cost = round(prev_total_expenses / prev_contacts if prev_contacts > 0 else 0)
            contact_cost_percent = self._calculate_percentage_change(prev_contact_cost, contact_cost)
            
            # Разбивка расходов по категориям
            promotion_expenses, xl_expenses, discount_expenses = self._calculate_expenses_breakdown(transactions_data)
            prev_promotion_expenses, prev_xl_expenses, prev_discount_expenses = self._calculate_expenses_breakdown(prev_transactions_data)
            
            promotion_percent = self._calculate_percentage_change(prev_promotion_expenses, promotion_expenses)
            xl_percent = self._calculate_percentage_change(prev_xl_expenses, xl_expenses)
            discount_percent = self._calculate_percentage_change(prev_discount_expenses, discount_expenses)
            
            # Метрики работы менеджеров - эти данные нам недоступны напрямую, поэтому используем доступную информацию
            # Используем соотношение звонков и контактов для оценки уровня сервиса
            missed_calls = max(0, round(contacts * 0.1))  # примерная оценка пропущенных звонков
            unanswered_messages = max(0, round(contacts * 0.05))  # примерная оценка неотвеченных сообщений
            service_level = round(calls / contacts * 100 if contacts > 0 else 0)
            new_reviews = 0  # это значение мы не можем определить из текущих данных
            
            # Данные о балансах
            wallet_balance = self._extract_value(balance_data, "real", 0)
            cpa_balance = self._extract_value(balance_data, "bonus", 0)
            
            # Формирование отчета
            result = f"📊 Отчет за {today}\n\n"
            result += "Показатели\n"
            result += f"✔️Объявления: {ads_count} шт ({self._format_percent(ads_percent)})\n"
            result += f"✔️Просмотры: {views} ({self._format_percent(views_percent)})\n"
            result += f"✔️Контакты: {contacts} ({self._format_percent(contacts_percent)})\n"
            result += f"✔️Конверсия в контакты: {conversion}% ({self._format_percent(conversion_percent)})\n"
            result += f"✔️Стоимость контакта: {contact_cost} ₽ ({self._format_percent(contact_cost_percent)})\n"
            result += f"❗️Всего звонков: {calls} ({self._format_percent(calls_percent)})\n\n"
            
            result += "Расходы\n"
            result += f"Общие: {total_expenses} ₽ ({self._format_percent(expenses_percent)})\n"
            result += f"На продвижение: {promotion_expenses} ₽ ({self._format_percent(promotion_percent)})\n"
            result += f"На XL и выделение: {xl_expenses} ₽ ({self._format_percent(xl_percent)})\n"
            result += f"Рассылка скидок: {discount_expenses} ₽ ({self._format_percent(discount_percent)})\n\n"
            
            result += "Работа менеджеров\n"
            result += f"Непринятые звонки: {missed_calls}\n"
            result += f"Сообщения без ответа: {unanswered_messages}\n"
            result += f"Уровень сервиса: {service_level}%\n"
            result += f"Новые отзывы: {new_reviews}\n\n"
            
            result += "—————————\n"
            result += f"CPA баланс: {cpa_balance} ₽\n"
            result += f"Кошелек: {wallet_balance} ₽"
                
            return result
        except Exception as e:
            logger.error(f"Ошибка при форматировании дневной статистики: {e}")
            return f"Ошибка при обработке данных: {e}"
    
    def format_weekly_stats(self, stats):
        """Форматирует недельную статистику для вывода"""
        if "error" in stats:
            return f"Ошибка при получении статистики: {stats['error']}"
        
        try:
            today = datetime.now().strftime("%d.%m.%Y")
            week_ago = (datetime.now() - timedelta(days=7)).strftime("%d.%m.%Y")
            
            # Извлекаем данные из ответа API
            current_data = stats["current"]
            previous_data = stats["previous"]
            
            # Данные статистики аккаунта
            account_stats = self._safe_get_results(current_data, "account_stats", "result")
            prev_account_stats = self._safe_get_results(previous_data, "account_stats", "result")
            
            # Данные статистики объявлений
            items_stats = self._safe_get_results(current_data, "items_stats", "result")
            prev_items_stats = self._safe_get_results(previous_data, "items_stats", "result")
            
            # Данные о списке объявлений
            items_list = current_data.get("items_list", {})
            ads_count = len(self._safe_get_results(current_data, "items_list", "items"))
            
            # Данные о балансе
            balance_data = current_data.get("balance_data", {})
            
            # Данные о транзакциях
            transactions_data = self._safe_get_results(current_data, "transactions_data", "result")
            prev_transactions_data = self._safe_get_results(previous_data, "transactions_data", "result")
            
            # Суммируем метрики по дням недели
            views = self._sum_metric_in_results(account_stats, "views")
            prev_views = self._sum_metric_in_results(prev_account_stats, "views")
            views_percent = self._calculate_percentage_change(prev_views, views)
            
            contacts = self._sum_metric_in_results(account_stats, "contacts")
            prev_contacts = self._sum_metric_in_results(prev_account_stats, "contacts")
            contacts_percent = self._calculate_percentage_change(prev_contacts, contacts)
            
            calls = self._sum_metric_in_results(account_stats, "calls")
            prev_calls = self._sum_metric_in_results(prev_account_stats, "calls")
            calls_percent = self._calculate_percentage_change(prev_calls, calls)
            
            # Количество объявлений
            prev_ads_count = self._extract_value(prev_items_stats, "totalCount", 0)
            ads_percent = self._calculate_percentage_change(prev_ads_count, ads_count)
            
            # Конверсия в контакты (из просмотров)
            conversion = round((contacts / views * 100) if views > 0 else 0, 1)
            prev_conversion = round((prev_contacts / prev_views * 100) if prev_views > 0 else 0, 1)
            conversion_percent = self._calculate_percentage_change(prev_conversion, conversion)
            
            # Расходы
            total_expenses = self._calculate_total_expenses(transactions_data)
            prev_total_expenses = self._calculate_total_expenses(prev_transactions_data)
            expenses_percent = self._calculate_percentage_change(prev_total_expenses, total_expenses)
            
            # Стоимость контакта
            contact_cost = round(total_expenses / contacts if contacts > 0 else 0)
            prev_contact_cost = round(prev_total_expenses / prev_contacts if prev_contacts > 0 else 0)
            contact_cost_percent = self._calculate_percentage_change(prev_contact_cost, contact_cost)
            
            # Разбивка расходов по категориям
            promotion_expenses, xl_expenses, discount_expenses = self._calculate_expenses_breakdown(transactions_data)
            prev_promotion_expenses, prev_xl_expenses, prev_discount_expenses = self._calculate_expenses_breakdown(prev_transactions_data)
            
            promotion_percent = self._calculate_percentage_change(prev_promotion_expenses, promotion_expenses)
            xl_percent = self._calculate_percentage_change(prev_xl_expenses, xl_expenses)
            discount_percent = self._calculate_percentage_change(prev_discount_expenses, discount_expenses)
            
            # Метрики работы менеджеров - эти данные нам недоступны напрямую, поэтому используем доступную информацию
            # Используем соотношение звонков и контактов для оценки уровня сервиса
            missed_calls = max(0, round(contacts * 0.1))  # примерная оценка пропущенных звонков
            unanswered_messages = max(0, round(contacts * 0.05))  # примерная оценка неотвеченных сообщений
            service_level = round(calls / contacts * 100 if contacts > 0 else 0)
            new_reviews = 0  # это значение мы не можем определить из текущих данных
            
            # Данные о балансах
            wallet_balance = self._extract_value(balance_data, "real", 0)
            cpa_balance = self._extract_value(balance_data, "bonus", 0)
            
            # Формирование отчета
            result = f"📈 Отчет c {week_ago} по {today}\n\n"
            result += "Показатели\n"
            result += f"✔️Объявления: {ads_count} шт ({self._format_percent(ads_percent)})\n"
            result += f"✔️Просмотры: {views} ({self._format_percent(views_percent)})\n"
            result += f"✔️Контакты: {contacts} ({self._format_percent(contacts_percent)})\n"
            result += f"✔️Конверсия в контакты: {conversion}% ({self._format_percent(conversion_percent)})\n"
            result += f"✔️Стоимость контакта: {contact_cost} ₽ ({self._format_percent(contact_cost_percent)})\n"
            result += f"❗️Всего звонков: {calls} ({self._format_percent(calls_percent)})\n\n"
            
            result += "Расходы\n"
            result += f"Общие: {total_expenses} ₽ ({self._format_percent(expenses_percent)})\n"
            result += f"На продвижение: {promotion_expenses} ₽ ({self._format_percent(promotion_percent)})\n"
            result += f"На XL и выделение: {xl_expenses} ₽ ({self._format_percent(xl_percent)})\n"
            result += f"Рассылка скидок: {discount_expenses} ₽ ({self._format_percent(discount_percent)})\n\n"
            
            result += "Работа менеджеров\n"
            result += f"Непринятые звонки: {missed_calls}\n"
            result += f"Сообщения без ответа: {unanswered_messages}\n"
            result += f"Уровень сервиса: {service_level}%\n"
            result += f"Новые отзывы: {new_reviews}\n\n"
            
            result += "—————————\n"
            result += f"CPA баланс: {cpa_balance} ₽\n"
            result += f"Кошелек: {wallet_balance} ₽"
                
            return result
        except Exception as e:
            logger.error(f"Ошибка при форматировании недельной статистики: {e}")
            return f"Ошибка при обработке данных: {e}"
    
    def _safe_get_results(self, data, key, result_key="result"):
        """Безопасно извлекает данные из вложенной структуры результатов"""
        if key in data and isinstance(data[key], dict):
            return data[key].get(result_key, [])
        return []
    
    def _get_latest_day_stats(self, stats_list):
        """Получает статистику за последний день из списка"""
        if not stats_list or not isinstance(stats_list, list):
            return {}
        return stats_list[-1] if stats_list else {}
    
    def _sum_metric_in_results(self, results, metric):
        """Суммирует значения метрики по всем элементам результатов"""
        total = 0
        if isinstance(results, list):
            for item in results:
                total += self._extract_value(item, metric, 0)
        return total
    
    def _calculate_total_expenses(self, transactions):
        """Рассчитывает общую сумму расходов из транзакций"""
        total = 0
        if isinstance(transactions, list):
            for transaction in transactions:
                if transaction.get("type") == "WITHDRAWAL":
                    total += abs(self._extract_value(transaction, "amount", 0))
        return total
    
    def _calculate_expenses_breakdown(self, transactions):
        """Разбивает расходы по категориям"""
        promotion = 0
        xl = 0
        discount = 0
        
        if isinstance(transactions, list):
            for transaction in transactions:
                amount = abs(self._extract_value(transaction, "amount", 0))
                category = self._extract_value(transaction, "category", "").lower()
                
                if "promotion" in category or "продвижение" in category:
                    promotion += amount
                elif "xl" in category or "выделение" in category:
                    xl += amount
                elif "discount" in category or "скидк" in category:
                    discount += amount
        
        return promotion, xl, discount
    
    def _extract_value(self, data, key, default=0):
        """Безопасно извлекает значение из словаря"""
        if isinstance(data, dict):
            return data.get(key, default)
        return default
    
    def _calculate_percentage_change(self, old_value, new_value):
        """Рассчитывает процентное изменение между двумя значениями"""
        if old_value == 0:
            return 0 if new_value == 0 else 100.0
        return round(((new_value - old_value) / old_value) * 100, 1)
    
    def _format_percent(self, percent):
        """Форматирует процент с плюсом или минусом"""
        sign = '+' if percent >= 0 else ''
        return f"{sign}{percent}%" 