from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


main_markup = InlineKeyboardMarkup()
main_markup.add(InlineKeyboardButton('📊 Дневной отчет', callback_data='daily_report'))
main_markup.add(InlineKeyboardButton('📈 Недельный отчет', callback_data='weekly_report'))
main_markup.add(InlineKeyboardButton('📅 Статистика за период', callback_data='stats_menu'))
