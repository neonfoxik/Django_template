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
from bot.texts import MAIN_TEXT, COINS_TRADE_TEXT
from bot.keyboards import main_markup
from .registration import start_registration


def start(message: Message) -> None:
    start_registration(message)


def menu_call(call: CallbackQuery) -> None:
    bot.edit_message_text(chat_id=call.message.chat.id, text=MAIN_TEXT, reply_markup=main_markup,
                          message_id=call.message.message_id)


def menu_m(message: Message) -> None:
    bot.send_message(chat_id=message.chat.id, text=MAIN_TEXT, reply_markup=main_markup)


def get_avito_report(api_key: str, date_from: str, date_to: str) -> dict:
    """Получение данных из API Авито"""
    headers = {
        'Authorization': f'Bearer {api_key}',
        'Content-Type': 'application/json'
    }
    
    # Здесь должен быть реальный запрос к API Авито
    # Это заглушка для примера
    response = {
        'ads_count': 10,
        'views': 1000,
        'contacts': 15,
        'calls': 10,
        'expenses': {
            'total': 5000,
            'promotion': 2000,
            'xl_highlight': 0,
            'discounts': 500
        },
        'managers': {
            'missed_calls': 1,
            'unanswered_messages': 0,
            'service_level': 78,
            'new_reviews': 0
        },
        'balance': {
            'cpa': 10500,
            'wallet': 20100
        },
        'changes': {
            'ads_count': 1.0,
            'views': 1.0,
            'contacts': 1.0,
            'conversion': 1.0,
            'contact_cost': 1.0,
            'calls': -10.0,
            'total_expenses': 1.0,
            'promotion_expenses': 1.0,
            'xl_expenses': 1.0,
            'discounts_expenses': 1.0
        }
    }
    
    return response


def generate_daily_report() -> str:
    """Генерация ежедневного отчета"""
    today = datetime.datetime.now()
    yesterday = today - datetime.timedelta(days=1)
    date_str = yesterday.strftime('%d.%m.%Y')
    
    # Получение данных из API Авито
    api_key = settings.AVITO_API_KEY
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


def generate_weekly_report() -> str:
    """Генерация еженедельного отчета"""
    today = datetime.datetime.now()
    week_start = today - datetime.timedelta(days=today.weekday() + 7)
    week_end = week_start + datetime.timedelta(days=6)
    
    # Получение данных из API Авито
    api_key = settings.AVITO_API_KEY
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
    """Отправка ежедневного отчета пользователю"""
    report = generate_daily_report()
    bot.send_message(chat_id=user_id, text=report)


def send_weekly_report(user_id: int) -> None:
    """Отправка еженедельного отчета пользователю"""
    report = generate_weekly_report()
    bot.send_message(chat_id=user_id, text=report)
