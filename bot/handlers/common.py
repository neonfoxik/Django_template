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
    """Получение данных из API Авито"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Базовый URL API Авито
    base_url = "https://api.avito.ru/stats/v1"
    
    # Получение данных о просмотрах и контактах
    views_url = f"{base_url}/views"
    contacts_url = f"{base_url}/contacts"
    calls_url = f"{base_url}/calls"
    expenses_url = f"{base_url}/expenses"
    balance_url = f"{base_url}/balance"
    
    params = {
        'date_from': date_from,
        'date_to': date_to,
        'group_by': 'day'
    }
    
    # Получение данных о просмотрах
    views_response = requests.get(views_url, headers=headers, params=params)
    views_data = views_response.json() if views_response.status_code == 200 else {'result': {'items': []}}
    
    # Получение данных о контактах
    contacts_response = requests.get(contacts_url, headers=headers, params=params)
    contacts_data = contacts_response.json() if contacts_response.status_code == 200 else {'result': {'items': []}}
    
    # Получение данных о звонках
    calls_response = requests.get(calls_url, headers=headers, params=params)
    calls_data = calls_response.json() if calls_response.status_code == 200 else {'result': {'items': []}}
    
    # Получение данных о расходах
    expenses_response = requests.get(expenses_url, headers=headers, params=params)
    expenses_data = expenses_response.json() if expenses_response.status_code == 200 else {'result': {'items': []}}
    
    # Получение данных о балансе
    balance_response = requests.get(balance_url, headers=headers)
    balance_data = balance_response.json() if balance_response.status_code == 200 else {'result': {}}
    
    # Получение данных о количестве объявлений
    ads_url = f"{base_url}/items"
    ads_response = requests.get(ads_url, headers=headers, params=params)
    ads_data = ads_response.json() if ads_response.status_code == 200 else {'result': {'items': []}}
    
    # Получение данных о работе менеджеров
    managers_url = f"{base_url}/managers"
    managers_response = requests.get(managers_url, headers=headers, params=params)
    managers_data = managers_response.json() if managers_response.status_code == 200 else {'result': {'items': []}}
    
    # Обработка полученных данных
    total_views = sum(item.get('views', 0) for item in views_data.get('result', {}).get('items', []))
    total_contacts = sum(item.get('contacts', 0) for item in contacts_data.get('result', {}).get('items', []))
    total_calls = sum(item.get('calls', 0) for item in calls_data.get('result', {}).get('items', []))
    ads_count = sum(item.get('count', 0) for item in ads_data.get('result', {}).get('items', []))
    
    # Расходы
    total_expenses = sum(item.get('total', 0) for item in expenses_data.get('result', {}).get('items', []))
    promotion_expenses = sum(item.get('promotion', 0) for item in expenses_data.get('result', {}).get('items', []))
    xl_expenses = sum(item.get('xl_highlight', 0) for item in expenses_data.get('result', {}).get('items', []))
    discounts_expenses = sum(item.get('discounts', 0) for item in expenses_data.get('result', {}).get('items', []))
    
    # Данные о менеджерах
    missed_calls = sum(item.get('missed_calls', 0) for item in managers_data.get('result', {}).get('items', []))
    unanswered_messages = sum(item.get('unanswered_messages', 0) for item in managers_data.get('result', {}).get('items', []))
    service_level = sum(item.get('service_level', 0) for item in managers_data.get('result', {}).get('items', []))
    new_reviews = sum(item.get('new_reviews', 0) for item in managers_data.get('result', {}).get('items', []))
    
    # Баланс
    cpa_balance = balance_data.get('result', {}).get('cpa', 0)
    wallet_balance = balance_data.get('result', {}).get('wallet', 0)
    
    # Получение данных за предыдущий период для расчета изменений
    prev_date_to = datetime.datetime.strptime(date_from, '%Y-%m-%d') - datetime.timedelta(days=1)
    prev_date_from = prev_date_to - (datetime.datetime.strptime(date_to, '%Y-%m-%d') - datetime.datetime.strptime(date_from, '%Y-%m-%d'))
    
    prev_params = {
        'date_from': prev_date_from.strftime('%Y-%m-%d'),
        'date_to': prev_date_to.strftime('%Y-%m-%d'),
        'group_by': 'day'
    }
    
    # Получение предыдущих данных для сравнения
    prev_views_response = requests.get(views_url, headers=headers, params=prev_params)
    prev_views_data = prev_views_response.json() if prev_views_response.status_code == 200 else {'result': {'items': []}}
    
    prev_contacts_response = requests.get(contacts_url, headers=headers, params=prev_params)
    prev_contacts_data = prev_contacts_response.json() if prev_contacts_response.status_code == 200 else {'result': {'items': []}}
    
    prev_calls_response = requests.get(calls_url, headers=headers, params=prev_params)
    prev_calls_data = prev_calls_response.json() if prev_calls_response.status_code == 200 else {'result': {'items': []}}
    
    prev_expenses_response = requests.get(expenses_url, headers=headers, params=prev_params)
    prev_expenses_data = prev_expenses_response.json() if prev_expenses_response.status_code == 200 else {'result': {'items': []}}
    
    prev_ads_response = requests.get(ads_url, headers=headers, params=prev_params)
    prev_ads_data = prev_ads_response.json() if prev_ads_response.status_code == 200 else {'result': {'items': []}}
    
    # Расчет предыдущих значений
    prev_total_views = sum(item.get('views', 0) for item in prev_views_data.get('result', {}).get('items', []))
    prev_total_contacts = sum(item.get('contacts', 0) for item in prev_contacts_data.get('result', {}).get('items', []))
    prev_total_calls = sum(item.get('calls', 0) for item in prev_calls_data.get('result', {}).get('items', []))
    prev_ads_count = sum(item.get('count', 0) for item in prev_ads_data.get('result', {}).get('items', []))
    
    prev_total_expenses = sum(item.get('total', 0) for item in prev_expenses_data.get('result', {}).get('items', []))
    prev_promotion_expenses = sum(item.get('promotion', 0) for item in prev_expenses_data.get('result', {}).get('items', []))
    prev_xl_expenses = sum(item.get('xl_highlight', 0) for item in prev_expenses_data.get('result', {}).get('items', []))
    prev_discounts_expenses = sum(item.get('discounts', 0) for item in prev_expenses_data.get('result', {}).get('items', []))
    
    # Расчет изменений в процентах
    def calculate_change(current, previous):
        if previous == 0:
            return 0.0
        return round(((current - previous) / previous) * 100, 1)
    
    # Расчет конверсии
    current_conversion = (total_contacts / total_views * 100) if total_views > 0 else 0
    prev_conversion = (prev_total_contacts / prev_total_views * 100) if prev_total_views > 0 else 0
    
    # Расчет стоимости контакта
    current_contact_cost = (total_expenses / total_contacts) if total_contacts > 0 else 0
    prev_contact_cost = (prev_total_expenses / prev_total_contacts) if prev_total_contacts > 0 else 0
    
    # Формирование результата
    result = {
        'ads_count': ads_count,
        'views': total_views,
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
            'wallet': wallet_balance
        },
        'changes': {
            'ads_count': calculate_change(ads_count, prev_ads_count),
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


def generate_daily_report(tg_id) -> str:
    """Генерация ежедневного отчета"""
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    date_str = yesterday.strftime('%d.%m.%Y')
    
    api_key = User.objects.get(telegram_id=tg_id).avito_api_key
    data = get_avito_report(api_key, yesterday.strftime('%Y-%m-%d'), yesterday.strftime('%Y-%m-%d'))
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


def generate_weekly_report(tg_id) -> str:
    """Генерация еженедельного отчета"""
    today = datetime.datetime.now()
    week_start = today - datetime.timedelta(days=today.weekday() + 7)
    week_end = week_start + datetime.timedelta(days=6)
    
    # Получение данных из API Авито
    api_key = User.objects.get(telegram_id=tg_id).avito_api_key
    data = get_avito_report(api_key, week_start.strftime('%Y-%m-%d'), week_end.strftime('%Y-%m-%d'))
    
    report = f"Еженедельный отчет ({week_start.strftime('%d.%m.%Y')} - {week_end.strftime('%d.%m.%Y')})\n\n"
    
    # Здесь формируется подробный еженедельный отчет
    # ...
    
    # Добавление расширенной аналитики
    report += "\nРасширенная аналитика за неделю:\n"
    report += "1. Анализ эффективности объявлений: наиболее просматриваемые категории - ...\n"
    report += "2. Рекомендации по оптимизации бюджета: ...\n"
    report += "3. Сравнение с конкурентами в категории: ...\n"
    report += "4. Прогноз на следующую неделю: ...\n"
    
    return report


def send_daily_report(user_id: int) -> None:
    report = generate_daily_report(user_id)
    bot.send_message(chat_id=user_id, text=report)


def send_weekly_report(user_id: int) -> None:
    """Отправка еженедельного отчета пользователю"""
    report = generate_weekly_report(user_id)
    bot.send_message(chat_id=user_id, text=report)
