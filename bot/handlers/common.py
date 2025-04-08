import os
import random
import datetime
import requests
from django.utils import timezone
from bot import bot
from django.conf import settings
from telebot.types import (
    Message,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    CallbackQuery,
)
from bot.models import User
from bot.texts import MAIN_TEXT
from bot.keyboards import main_markup
from .registration import start_registration


def start(message: Message) -> None:
    start_registration(message)


def menu_call(call: CallbackQuery) -> None:
    bot.edit_message_text(chat_id=call.message.chat.id, text=MAIN_TEXT, reply_markup=main_markup,
                          message_id=call.message.message_id)


def menu_m(message: Message) -> None:
    bot.send_message(chat_id=message.chat.id, text=MAIN_TEXT, reply_markup=main_markup)

def daily_report(call: CallbackQuery) -> None:
    user_id = call.from_user.id
    send_daily_report(user_id)

def weekly_report(call: CallbackQuery) -> None:
    user_id = call.from_user.id
    send_weekly_report(user_id)

def get_avito_report(api_key: str, date_from: str, date_to: str) -> dict:
    """
    Получение данных из API Авито
    
    Примечание: Пользователь должен ввести секретный ключ API Авито (Client Secret),
    который можно получить в личном кабинете Авито в разделе "API" после регистрации
    приложения. Ключ имеет формат: af0deccbgcgidddjgnvljitntccdduijhdinfgjgfjir
    """
    try:
        headers = {
            'Authorization': f'Bearer {api_key}',
            'Content-Type': 'application/json'
        }
        
        # Базовый URL API Авито
        base_url = "https://api.avito.ru/core/v1"
        
        # Получение данных о просмотрах и контактах
        views_url = f"{base_url}/items/stats"
        contacts_url = f"{base_url}/items/stats"
        
        # Параметры запроса для статистики
        stats_params = {
            'dateFrom': date_from,
            'dateTo': date_to,
            'fields': 'views,contacts,calls,favorites'
        }
        
        # Получение данных о статистике объявлений
        stats_response = requests.get(views_url, headers=headers, params=stats_params)
        stats_data = stats_response.json() if stats_response.status_code == 200 else {'result': []}
        
        # Получение данных о балансе
        balance_url = f"{base_url}/account/balance"
        balance_response = requests.get(balance_url, headers=headers)
        balance_data = balance_response.json() if balance_response.status_code == 200 else {'balance': 0}
        
        # Получение данных о количестве объявлений
        items_url = f"{base_url}/items"
        items_params = {
            'per_page': 100,  # Максимальное количество объявлений на страницу
            'page': 1
        }
        items_response = requests.get(items_url, headers=headers, params=items_params)
        items_data = items_response.json() if items_response.status_code == 200 else {'result': {'items': []}}
        
        # Обработка полученных данных
        total_views = 0
        total_contacts = 0
        total_calls = 0
        daily_views = []
        
        # Обработка статистики
        if 'result' in stats_data:
            for item in stats_data['result']:
                total_views += item.get('views', 0)
                total_contacts += item.get('contacts', 0)
                total_calls += item.get('calls', 0)
                
                # Добавление ежедневных просмотров
                if 'dailyStats' in item:
                    for day_stat in item['dailyStats']:
                        date_str = day_stat.get('date', '')
                        views = day_stat.get('views', 0)
                        daily_views.append({
                            'date': date_str,
                            'views': views
                        })
        
        # Подсчет количества объявлений
        ads_count = 0
        if 'result' in items_data and 'items' in items_data['result']:
            ads_count = len(items_data['result']['items'])
            
            # Если есть пагинация, получаем общее количество объявлений
            if 'pagination' in items_data['result'] and 'total' in items_data['result']['pagination']:
                ads_count = items_data['result']['pagination']['total']
        
        # Получение данных за предыдущий период для расчета изменений
        prev_date_to = datetime.datetime.strptime(date_from, '%Y-%m-%d') - datetime.timedelta(days=1)
        prev_date_from = prev_date_to - (datetime.datetime.strptime(date_to, '%Y-%m-%d') - datetime.datetime.strptime(date_from, '%Y-%m-%d'))
        
        prev_stats_params = {
            'dateFrom': prev_date_from.strftime('%Y-%m-%d'),
            'dateTo': prev_date_to.strftime('%Y-%m-%d'),
            'fields': 'views,contacts,calls,favorites'
        }
        
        # Получение предыдущих данных для сравнения
        prev_stats_response = requests.get(views_url, headers=headers, params=prev_stats_params)
        prev_stats_data = prev_stats_response.json() if prev_stats_response.status_code == 200 else {'result': []}
        
        # Обработка предыдущих данных
        prev_total_views = 0
        prev_total_contacts = 0
        prev_total_calls = 0
        
        if 'result' in prev_stats_data:
            for item in prev_stats_data['result']:
                prev_total_views += item.get('views', 0)
                prev_total_contacts += item.get('contacts', 0)
                prev_total_calls += item.get('calls', 0)
        
        # Расчет изменений в процентах
        def calculate_change(current, previous):
            if previous == 0:
                return 0.0
            return round(((current - previous) / previous) * 100, 1)
        
        # Расчет конверсии
        current_conversion = (total_contacts / total_views * 100) if total_views > 0 else 0
        prev_conversion = (prev_total_contacts / prev_total_views * 100) if prev_total_views > 0 else 0
        
        # Получение данных о расходах из API
        expenses_url = f"{base_url}/account/expenses"
        expenses_params = {
            'dateFrom': date_from,
            'dateTo': date_to
        }
        expenses_response = requests.get(expenses_url, headers=headers, params=expenses_params)
        expenses_data = expenses_response.json() if expenses_response.status_code == 200 else {}
        
        # Получение данных о предыдущих расходах
        prev_expenses_params = {
            'dateFrom': prev_date_from.strftime('%Y-%m-%d'),
            'dateTo': prev_date_to.strftime('%Y-%m-%d')
        }
        prev_expenses_response = requests.get(expenses_url, headers=headers, params=prev_expenses_params)
        prev_expenses_data = prev_expenses_response.json() if prev_expenses_response.status_code == 200 else {}
        
        # Извлечение данных о расходах
        total_expenses = expenses_data.get('total', 0)
        promotion_expenses = expenses_data.get('promotion', 0)
        xl_expenses = expenses_data.get('xl', 0)
        discounts_expenses = expenses_data.get('discounts', 0)
        
        prev_total_expenses = prev_expenses_data.get('total', 0)
        prev_promotion_expenses = prev_expenses_data.get('promotion', 0)
        prev_xl_expenses = prev_expenses_data.get('xl', 0)
        prev_discounts_expenses = prev_expenses_data.get('discounts', 0)
        
        # Получение данных о работе менеджеров
        managers_url = f"{base_url}/managers/stats"
        managers_params = {
            'dateFrom': date_from,
            'dateTo': date_to
        }
        managers_response = requests.get(managers_url, headers=headers, params=managers_params)
        managers_data = managers_response.json() if managers_response.status_code == 200 else {}
        
        # Извлечение данных о работе менеджеров
        missed_calls = managers_data.get('missed_calls', 0)
        unanswered_messages = managers_data.get('unanswered_messages', 0)
        service_level = managers_data.get('service_level', 0)
        new_reviews = managers_data.get('new_reviews', 0)
        
        # Получение данных о CPA балансе
        cpa_url = f"{base_url}/account/cpa/balance"
        cpa_response = requests.get(cpa_url, headers=headers)
        cpa_data = cpa_response.json() if cpa_response.status_code == 200 else {}
        cpa_balance = cpa_data.get('balance', 0)
        
        # Расчет стоимости контакта
        current_contact_cost = (total_expenses / total_contacts) if total_contacts > 0 else 0
        prev_contact_cost = (prev_total_expenses / prev_total_contacts) if prev_total_contacts > 0 else 0
        
        # Формирование результата
        result = {
            'ads_count': ads_count,
            'views': total_views,
            'daily_views': daily_views,
            'contacts': total_contacts,
            'calls': total_calls,
            'expenses': {
                'total': total_expenses,
                'promotion': promotion_expenses,
                'xl_highlight': xl_expenses,
                'discounts': discounts_expenses
            },
            'managers': {
                'missed_calls': missed_calls,
                'unanswered_messages': unanswered_messages,
                'service_level': service_level,
                'new_reviews': new_reviews
            },
            'balance': {
                'cpa': cpa_balance,
                'wallet': balance_data.get('balance', 0)
            },
            'changes': {
                'ads_count': calculate_change(ads_count, ads_count),  # Предполагаем, что количество объявлений не изменилось
                'views': calculate_change(total_views, prev_total_views),
                'contacts': calculate_change(total_contacts, prev_total_contacts),
                'conversion': calculate_change(current_conversion, prev_conversion),
                'contact_cost': calculate_change(current_contact_cost, prev_contact_cost),
                'calls': calculate_change(total_calls, prev_total_calls),
                'total_expenses': calculate_change(total_expenses, prev_total_expenses),
                'promotion_expenses': calculate_change(promotion_expenses, prev_promotion_expenses),
                'xl_expenses': calculate_change(xl_expenses, prev_xl_expenses),
                'discounts_expenses': calculate_change(discounts_expenses, prev_discounts_expenses)
            }
        }
        
        return result
    except Exception as e:
        print(f"Ошибка при получении данных из API Авито: {e}")
        return {
            'error': str(e)
        }


def generate_daily_report(tg_id) -> str:
    """Генерация ежедневного отчета"""
    try:
        today = datetime.datetime.now()
        yesterday = today - datetime.timedelta(days=1)
        date_str = yesterday.strftime('%d.%m.%Y')
        
        api_key = User.objects.get(telegram_id=tg_id).avito_api_key
        data = get_avito_report(api_key, yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d'))
        
        if 'error' in data:
            return f"Ошибка при получении данных: {data['error']}"
        
        # Расчет конверсии
        conversion = round((data['contacts'] / data['views']) * 100, 1) if data['views'] > 0 else 0
        # Расчет стоимости контакта
        contact_cost = round(data['expenses']['total'] / data['contacts']) if data['contacts'] > 0 else 0
        
        report = f"Отчет за {date_str}\n\n"
        
        report += "Показатели\n"
        report += f"✔️Объявления: {data['ads_count']} шт ({'+' if data['changes']['ads_count'] >= 0 else ''}{data['changes']['ads_count']}%)\n"
        report += f"✔️Просмотры: {data['views']} ({'+' if data['changes']['views'] >= 0 else ''}{data['changes']['views']}%)\n"
        report += f"✔️Контакты: {data['contacts']} ({'+' if data['changes']['contacts'] >= 0 else ''}{data['changes']['contacts']}%)\n"
        report += f"✔️Конверсия в контакты: {conversion}% ({'+' if data['changes']['conversion'] >= 0 else ''}{data['changes']['conversion']}%)\n"
        report += f"✔️Стоимость контакта: {contact_cost} ₽ ({'+' if data['changes']['contact_cost'] >= 0 else ''}{data['changes']['contact_cost']}%)\n"
        report += f"❗️Всего звонков: {data['calls']} ({'+' if data['changes']['calls'] >= 0 else ''}{data['changes']['calls']}%)\n\n"
        
        report += "Расходы\n"
        report += f"Общие: {data['expenses']['total']} ₽ ({'+' if data['changes']['total_expenses'] >= 0 else ''}{data['changes']['total_expenses']}%)\n"
        report += f"На продвижение: {data['expenses']['promotion']} ₽ ({'+' if data['changes']['promotion_expenses'] >= 0 else ''}{data['changes']['promotion_expenses']}%)\n"
        report += f"На XL и выделение: {data['expenses']['xl_highlight']} ₽ ({'+' if data['changes']['xl_expenses'] >= 0 else ''}{data['changes']['xl_expenses']}%)\n"
        report += f"Рассылка скидок: {data['expenses']['discounts']} ₽ ({'+' if data['changes']['discounts_expenses'] >= 0 else ''}{data['changes']['discounts_expenses']}%)\n\n"
        
        report += "Работа менеджеров\n"
        report += f"Непринятые звонки: {data['managers']['missed_calls']}\n"
        report += f"Сообщения без ответа: {data['managers']['unanswered_messages']}\n"
        report += f"Уровень сервиса: {data['managers']['service_level']}%\n"
        report += f"Новые отзывы: {data['managers']['new_reviews']}\n\n"
        
        report += "—————————\n"
        report += f"CPA баланс: {data['balance']['cpa']} ₽\n"
        report += f"Кошелек: {data['balance']['wallet']} ₽\n"
        
        # Добавление аналитических комментариев
        report += "\nАналитика:\n"
        if data['changes']['calls'] < 0:
            report += "⚠️ Снижение количества звонков требует внимания. Возможно, стоит пересмотреть стратегию размещения объявлений.\n"
        
        if conversion < 3:
            report += "⚠️ Низкая конверсия в контакты. Рекомендуется улучшить качество фотографий и описаний объявлений.\n"
        
        if data['managers']['missed_calls'] > 0:
            report += f"⚠️ {data['managers']['missed_calls']} пропущенных звонков. Необходимо улучшить работу менеджеров.\n"
        
        return report
    except Exception as e:
        return f"Ошибка при генерации отчета: {str(e)}"


def generate_weekly_report(tg_id) -> str:
    """Генерация еженедельного отчета"""
    try:
        today = datetime.datetime.now()
        # Получаем понедельник прошлой недели
        week_start = today - datetime.timedelta(days=today.weekday() + 7)
        # Получаем воскресенье прошлой недели
        week_end = week_start + datetime.timedelta(days=6)
        
        # Получение данных из API Авито
        api_key = User.objects.get(telegram_id=tg_id).avito_api_key
        data = get_avito_report(api_key, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))
        
        if 'error' in data:
            return f"Ошибка при получении данных: {data['error']}"
        
        report = f"Еженедельный отчет ({week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')})\n\n"
        
        # Добавляем информацию о просмотрах по дням недели
        report += "Просмотры по дням недели:\n"
        
        # Создаем словарь для хранения просмотров по дням недели
        weekdays = {
            0: "Понедельник",
            1: "Вторник",
            2: "Среда",
            3: "Четверг",
            4: "Пятница",
            5: "Суббота",
            6: "Воскресенье"
        }
        
        # Сортируем просмотры по дате
        daily_views = sorted(data['daily_views'], key=lambda x: x['date'])
        
        # Выводим просмотры по дням
        for view_data in daily_views:
            date_obj = datetime.datetime.strptime(view_data['date'], '%Y-%m-%d')
            weekday = weekdays[date_obj.weekday()]
            report += f"{weekday} ({date_obj.strftime('%d.%m')}): {view_data['views']} просмотров\n"
        
        report += "\nОбщая статистика за неделю:\n"
        report += f"Всего просмотров: {data['views']}\n"
        report += f"Всего контактов: {data['contacts']}\n"
        report += f"Всего звонков: {data['calls']}\n"
        report += f"Количество объявлений: {data['ads_count']}\n\n"
        
        # Расчет конверсии
        conversion = round((data['contacts'] / data['views']) * 100, 1) if data['views'] > 0 else 0
        report += f"Конверсия в контакты: {conversion}%\n"
        
        # Расчет стоимости контакта
        contact_cost = round(data['expenses']['total'] / data['contacts']) if data['contacts'] > 0 else 0
        report += f"Стоимость контакта: {contact_cost} ₽\n\n"
        
        report += "Расходы за неделю:\n"
        report += f"Общие: {data['expenses']['total']} ₽\n"
        report += f"На продвижение: {data['expenses']['promotion']} ₽\n"
        report += f"На XL и выделение: {data['expenses']['xl_highlight']} ₽\n"
        report += f"Рассылка скидок: {data['expenses']['discounts']} ₽\n\n"
        
        report += "Работа менеджеров за неделю:\n"
        report += f"Непринятые звонки: {data['managers']['missed_calls']}\n"
        report += f"Сообщения без ответа: {data['managers']['unanswered_messages']}\n"
        report += f"Уровень сервиса: {data['managers']['service_level']}%\n"
        report += f"Новые отзывы: {data['managers']['new_reviews']}\n\n"
        
        report += "—————————\n"
        report += f"CPA баланс: {data['balance']['cpa']} ₽\n"
        report += f"Кошелек: {data['balance']['wallet']} ₽\n"
        
        # Добавление расширенной аналитики
        report += "\nРасширенная аналитика за неделю:\n"
        
        # Анализ лучших и худших дней по просмотрам
        if daily_views:
            best_day = max(daily_views, key=lambda x: x['views'])
            worst_day = min(daily_views, key=lambda x: x['views'])
            best_date = datetime.datetime.strptime(best_day['date'], '%Y-%m-%d')
            worst_date = datetime.datetime.strptime(worst_day['date'], '%Y-%m-%d')
            
            report += f"1. Лучший день по просмотрам: {weekdays[best_date.weekday()]} ({best_date.strftime('%d.%m')}) - {best_day['views']} просмотров\n"
            report += f"2. Худший день по просмотрам: {weekdays[worst_date.weekday()]} ({worst_date.strftime('%d.%m')}) - {worst_day['views']} просмотров\n"
        
        # Рекомендации по оптимизации
        report += "3. Рекомендации по оптимизации:\n"
        if conversion < 3:
            report += "   - Улучшить качество фотографий и описаний объявлений\n"
        if data['managers']['missed_calls'] > 5:
            report += "   - Улучшить работу менеджеров по приему звонков\n"
        if data['managers']['unanswered_messages'] > 5:
            report += "   - Улучшить работу с сообщениями клиентов\n"
        
        return report
    except Exception as e:
        return f"Ошибка при генерации еженедельного отчета: {str(e)}"


def send_daily_report(user_id: int) -> None:
    try:
        report = generate_daily_report(user_id)
        bot.send_message(chat_id=user_id, text=report)
    except Exception as e:
        bot.send_message(chat_id=user_id, text=f"Ошибка при отправке ежедневного отчета: {str(e)}")


def send_weekly_report(user_id: int) -> None:
    """Отправка еженедельного отчета пользователю"""
    try:
        report = generate_weekly_report(user_id)
        bot.send_message(chat_id=user_id, text=report)
    except Exception as e:
        bot.send_message(chat_id=user_id, text=f"Ошибка при отправке еженедельного отчета: {str(e)}")
