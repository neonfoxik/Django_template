from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


main_markup = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton("Профиль", callback_data="profile")
btn2 = InlineKeyboardButton("Отчет за неделю", callback_data="weekly_report")
btn3 = InlineKeyboardButton("Отчет за день", callback_data="daily_report")
main_markup.add(btn1).add(btn2).add(btn3)
