from bot import bot
from bot.keyboards import main_markup
from bot.avito_api import get_daily_views

def start(message):
    """Обработчик команды /start"""
    bot.send_message(
        message.chat.id,
        "Добро пожаловать! Выберите действие:",
        reply_markup=main_markup
    )

def menu_call(call):
    """Обработчик нажатия на кнопки меню"""
    bot.answer_callback_query(call.id)
    menu_m(call.message)

def menu_m(message):
    """Отображение главного меню"""
    bot.send_message(
        message.chat.id,
        "Выберите действие:",
        reply_markup=main_markup
    )

def daily_report(call):
    """Обработчик кнопки 'Отчет за день'"""
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Получение информации о вашем аккаунте Авито...")
    result = get_daily_views(call.from_user.id)
    bot.send_message(call.message.chat.id, result)

def weekly_report(call):
    """Обработчик кнопки 'Отчет за неделю'"""
    bot.answer_callback_query(call.id)
    bot.send_message(call.message.chat.id, "Функция отчета за неделю в разработке")
