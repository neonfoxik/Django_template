from telebot.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)


main_markup = InlineKeyboardMarkup()
btn1 = InlineKeyboardButton("Профиль", callback_data="profile")
btn2 = InlineKeyboardButton("Монеты???", callback_data="coins_menu")
btn3 = InlineKeyboardButton("Рефералка", callback_data="referal_menu")
btn4 = InlineKeyboardButton("Туториал", callback_data="FAQ")
main_markup.add(btn1, btn2).add(btn3, btn4)
