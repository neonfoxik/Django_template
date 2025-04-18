from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


main_markup = InlineKeyboardMarkup()
btn2 = InlineKeyboardButton("Отчет за неделю", callback_data="weekly_report")
btn3 = InlineKeyboardButton("Отчет за день", callback_data="daily_report")
main_markup.add(btn2).add(btn3)
