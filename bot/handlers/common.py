from bot import bot
from bot.models import User, AvitoAccount, UserAvitoAccount
from bot.keyboards import main_markup
from bot.texts import MAIN_TEXT
from bot.services import get_daily_statistics, get_weekly_statistics
import telebot
from django.db import models

import logging

logger = logging.getLogger(__name__)

def start(message):
    """Обработчик команды /start"""
    from bot.handlers.registration import start_registration
    start_registration(message)

def menu_m(message):
    """Главное меню"""
    chat_id = message.chat.id if hasattr(message, 'chat') else message.from_user.id
    bot.send_message(
        chat_id=chat_id,
        text=MAIN_TEXT,
        reply_markup=main_markup
    )

def format_expenses_message(expenses):
    """Форматирует сообщение о расходах"""
    if not expenses:
        return "0.00 ₽"
        
    # Проверяем правильность структуры
    if not isinstance(expenses, dict):
        return "0.00 ₽"
        
    total = expenses.get('total', 0)
    details = expenses.get('details', {})
    
    if total <= 0:
        return "0.00 ₽"
    
    message = f"{total:.2f} ₽\n"
    
    # Добавляем детализацию расходов, если они есть
    if details:
        message += f"📋 *Детализация расходов:*\n"
        
        # Сортируем по убыванию суммы
        sorted_details = sorted(
            details.items(), 
            key=lambda x: x[1]['amount'], 
            reverse=True
        )
        
        for service, service_details in sorted_details:
            amount = service_details.get('amount', 0)
            count = service_details.get('count', 1)
            items = service_details.get('items', [])
            
            # Количество объявлений, если есть
            items_count = len(items) if items else 0
            items_suffix = ""
            if items_count > 0:
                items_suffix = f" ({items_count} объявл.)"
            
            message += f"   • {service}{items_suffix}: {amount:.2f} ₽ ({count} опер.)\n"
    
    return message

def select_avito_account(chat_id, user_id, callback_prefix):
    """Отображает выбор аккаунтов Авито для пользователя"""
    try:
        # Детальное логирование для отладки
        logger.info(f"ОТЛАДКА: select_avito_account вызван для пользователя {user_id}, chat_id: {chat_id}")
        
        # Получаем пользователя
        user = User.objects.filter(telegram_id=user_id).first()
        
        logger.info(f"ОТЛАДКА: Найден пользователь: {user}")
        
        if not user:
            bot.send_message(chat_id, "❌ Вы не зарегистрированы. Используйте /start для регистрации.")
            return
        
        # Получаем все аккаунты Авито в системе
        accounts = AvitoAccount.objects.filter(
            client_id__isnull=False,
            client_secret__isnull=False
        ).exclude(client_id="none").distinct()
        
        logger.info(f"ОТЛАДКА: Найдено аккаунтов Авито: {accounts.count()}")
        
        if not accounts.exists():
            bot.send_message(chat_id, "❌ В системе нет зарегистрированных аккаунтов Авито")
            logger.error(f"Нет аккаунтов в системе")
            return
            
        if accounts.count() == 1:
            # Если только один аккаунт, сразу используем его
            account_id = accounts.first().id
            logger.info(f"ОТЛАДКА: Найден один аккаунт: {account_id}, используем его напрямую")
            if callback_prefix == "daily_report":
                daily_report_for_account(chat_id, account_id)
            else:
                weekly_report_for_account(chat_id, account_id)
            return
            
        # Создаем клавиатуру для выбора аккаунта
        markup = telebot.types.InlineKeyboardMarkup()
        for account in accounts:
            button = telebot.types.InlineKeyboardButton(
                text=account.name,
                callback_data=f"{callback_prefix}_{account.id}"
            )
            markup.add(button)
            logger.info(f"ОТЛАДКА: Добавлена кнопка для аккаунта {account.id}: {account.name}, callback_data: {callback_prefix}_{account.id}")
            
        bot.send_message(
            chat_id=chat_id,
            text="Выберите аккаунт Авито для отчета:",
            reply_markup=markup
        )
    except User.DoesNotExist:
        bot.send_message(chat_id, "❌ Вы не зарегистрированы. Используйте /start для регистрации.")
    except Exception as e:
        logger.error(f"Ошибка при выборе аккаунта: {e}")
        logger.exception("Полный стек-трейс ошибки:")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")

def daily_report(call):
    """Обработчик для получения дневного отчета"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    logger.info(f"ОТЛАДКА: daily_report вызван, user_id: {user_id}, chat_id: {chat_id}")
    
    # Проверяем, есть ли в callback_data идентификатор аккаунта
    parts = call.data.split("_")
    if len(parts) > 2 and parts[0] == "daily" and parts[1] == "report":
        # Если формат daily_report_ID, получаем отчет для конкретного аккаунта
        try:
            account_id = int(parts[2])
            daily_report_for_account(chat_id, account_id)
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка при обработке callback_data: {e}")
            bot.send_message(chat_id, "❌ Ошибка при обработке запроса. Пожалуйста, попробуйте снова.")
    else:
        # Иначе предлагаем выбрать аккаунт
        select_avito_account(chat_id, user_id, "daily_report")

def weekly_report(call):
    """Обработчик для получения недельного отчета"""
    chat_id = call.message.chat.id
    user_id = call.from_user.id
    
    logger.info(f"ОТЛАДКА: weekly_report вызван, user_id: {user_id}, chat_id: {chat_id}")
    
    # Проверяем, есть ли в callback_data идентификатор аккаунта
    parts = call.data.split("_")
    if len(parts) > 2 and parts[0] == "weekly" and parts[1] == "report":
        # Если формат weekly_report_ID, получаем отчет для конкретного аккаунта
        try:
            account_id = int(parts[2])
            weekly_report_for_account(chat_id, account_id)
        except (ValueError, IndexError) as e:
            logger.error(f"Ошибка при обработке callback_data: {e}")
            bot.send_message(chat_id, "❌ Ошибка при обработке запроса. Пожалуйста, попробуйте снова.")
    else:
        # Иначе предлагаем выбрать аккаунт
        select_avito_account(chat_id, user_id, "weekly_report")

def daily_report_for_account(chat_id, account_id):
    """Отправка дневного отчета для конкретного аккаунта"""
    # Отправляем сообщение о загрузке и сохраняем его ID
    loading_message = bot.send_message(chat_id, "⏳ Получаем данные из API Авито...")
    
    try:
        account = AvitoAccount.objects.get(id=account_id)
        client_id = account.client_id
        client_secret = account.client_secret
        response = get_daily_statistics(client_id, client_secret)
        
        # Удаляем сообщение о загрузке после получения данных
        bot.delete_message(chat_id, loading_message.message_id)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📊 *Статистика за {response['date']} - {account.name}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:*\n"
        message_text += f"   • Новых за день: {response['chats']['total']}\n"
        message_text += f"📱 *Показов телефона:* {response['phones_received']}\n\n"
        
        message_text += f"⭐ *Рейтинг:* {response['rating']}\n"
        message_text += f"👍 *Отзывы:*\n"
        message_text += f"   • Всего: {response['reviews']['total']}\n"
        message_text += f"   • За сегодня: {response['reviews']['today']}\n\n"
        
        message_text += f"📝 *Объявления:*\n"
        message_text += f"   • Всего: {response['items']['total']}\n"
        
        message_text += f"👁 *Просмотры:* {response['statistics']['views']}\n"
        message_text += f"📲 *Контакты:* {response['statistics']['contacts']}\n"
        message_text += f"❤️ *В избранном:* {response['statistics']['favorites']}\n\n"
        
        message_text += f"💰 *Финансы:*\n"
        message_text += f"   • Реальный баланс: {response['balance_real']} ₽\n"
        message_text += f"   • Бонусы: {response['balance_bonus']} ₽\n"
        message_text += f"   • Аванс: {response['advance']} ₽\n\n"
        
        message_text += f"💸 *Расходы за сегодня:* "
        
        # Добавляем расходы и детализацию
        expenses_message = format_expenses_message(response.get('expenses', {}))
        message_text += expenses_message
        
        bot.send_message(chat_id, message_text, parse_mode="Markdown")
        
    except AvitoAccount.DoesNotExist:
        # Удаляем сообщение о загрузке в случае ошибки
        bot.delete_message(chat_id, loading_message.message_id)
        bot.send_message(chat_id, "❌ Ошибка: аккаунт не найден")
    except Exception as e:
        # Удаляем сообщение о загрузке в случае ошибки
        try:
            bot.delete_message(chat_id, loading_message.message_id)
        except:
            pass
        logger.error(f"Ошибка при получении дневного отчета: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")

def weekly_report_for_account(chat_id, account_id):
    """Отправка недельного отчета для конкретного аккаунта"""
    # Отправляем сообщение о загрузке и сохраняем его ID
    loading_message = bot.send_message(chat_id, "⏳ Получаем данные из API Авито...")
    
    try:
        account = AvitoAccount.objects.get(id=account_id)
        client_id = account.client_id
        client_secret = account.client_secret
        response = get_weekly_statistics(client_id, client_secret)
        
        # Удаляем сообщение о загрузке после получения данных
        bot.delete_message(chat_id, loading_message.message_id)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📈 *Статистика за период: {response['period']} - {account.name}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:*\n"
        message_text += f"   • Новых за неделю: {response['chats']['total']}\n"
        message_text += f"📱 *Показов телефона:* {response['phones_received']}\n\n"
        
        message_text += f"⭐ *Рейтинг:* {response['rating']}\n"
        message_text += f"👍 *Отзывы:*\n"
        message_text += f"   • Всего: {response['reviews']['total']}\n"
        message_text += f"   • За неделю: {response['reviews']['weekly']}\n\n"
        
        message_text += f"📝 *Объявления:*\n"
        
        message_text += f"👁 *Просмотры:* {response['statistics']['views']}\n"
        message_text += f"📲 *Контакты:* {response['statistics']['contacts']}\n"
        message_text += f"❤️ *В избранном:* {response['statistics']['favorites']}\n\n"
        
        message_text += f"💰 *Финансы:*\n"
        message_text += f"   • Реальный баланс: {response['balance_real']} ₽\n"
        message_text += f"   • Бонусы: {response['balance_bonus']} ₽\n"
        message_text += f"   • Аванс: {response['advance']} ₽\n\n"
        
        message_text += f"💸 *Расходы за неделю:* "
        
        # Добавляем расходы и детализацию
        expenses_message = format_expenses_message(response.get('expenses', {}))
        message_text += expenses_message
        
        bot.send_message(chat_id, message_text, parse_mode="Markdown")
        
    except AvitoAccount.DoesNotExist:
        # Удаляем сообщение о загрузке в случае ошибки
        bot.delete_message(chat_id, loading_message.message_id)
        bot.send_message(chat_id, "❌ Ошибка: аккаунт не найден")
    except Exception as e:
        # Удаляем сообщение о загрузке в случае ошибки
        try:
            bot.delete_message(chat_id, loading_message.message_id)
        except:
            pass
        logger.error(f"Ошибка при получении недельного отчета: {e}")
        bot.send_message(chat_id, f"❌ Произошла ошибка: {str(e)}")

def send_daily_report(telegram_id, account_id):
    """Отправка дневного отчета по ID в Telegram и ID аккаунта Авито"""
    try:
        account = AvitoAccount.objects.get(id=account_id)
        client_id = account.client_id
        client_secret = account.client_secret
        response = get_daily_statistics(client_id, client_secret)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📊 *Статистика за {response['date']} - {account.name}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:*\n"
        message_text += f"   • Новых за день: {response['chats']['total']}\n"
        message_text += f"📱 *Показов телефона:* {response['phones_received']}\n\n"
        
        message_text += f"⭐ *Рейтинг:* {response['rating']}\n"
        message_text += f"👍 *Отзывы:*\n"
        message_text += f"   • Всего: {response['reviews']['total']}\n"
        message_text += f"   • За сегодня: {response['reviews']['today']}\n\n"
        
        message_text += f"📝 *Объявления:*\n"
        message_text += f"   • Всего: {response['items']['total']}\n"
        
        message_text += f"👁 *Просмотры:* {response['statistics']['views']}\n"
        message_text += f"📲 *Контакты:* {response['statistics']['contacts']}\n"
        message_text += f"❤️ *В избранном:* {response['statistics']['favorites']}\n\n"
        
        message_text += f"💰 *Финансы:*\n"
        message_text += f"   • Реальный баланс: {response['balance_real']} ₽\n"
        message_text += f"   • Бонусы: {response['balance_bonus']} ₽\n"
        message_text += f"   • Аванс: {response['advance']} ₽\n\n"
        
        message_text += f"💸 *Расходы за сегодня:* "
        
        # Добавляем расходы и детализацию
        expenses_message = format_expenses_message(response.get('expenses', {}))
        message_text += expenses_message

        # Отправляем отчет на указанный ID для дневных отчетов
        bot.send_message(telegram_id, message_text, parse_mode="Markdown")
        
    except AvitoAccount.DoesNotExist:
        logger.error(f"Аккаунт с ID {account_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке дневного отчета: {e}")

def send_weekly_report(telegram_id, account_id):
    """Отправка недельного отчета по ID в Telegram и ID аккаунта Авито"""
    try:
        account = AvitoAccount.objects.get(id=account_id)
        client_id = account.client_id
        client_secret = account.client_secret
        response = get_weekly_statistics(client_id, client_secret)
        
        # Формируем читаемое сообщение для пользователя
        message_text = f"📈 *Статистика за период: {response['period']} - {account.name}*\n\n"
        message_text += f"📞 *Звонки:*\n"
        message_text += f"   • Всего: {response['calls']['total']}\n"
        message_text += f"   • Отвечено: {response['calls']['answered']}\n"
        message_text += f"   • Пропущено: {response['calls']['missed']}\n\n"
        
        message_text += f"💬 *Сообщения:*\n"
        message_text += f"   • Новых за неделю: {response['chats']['total']}\n"
        message_text += f"📱 *Показов телефона:* {response['phones_received']}\n\n"
        
        message_text += f"⭐ *Рейтинг:* {response['rating']}\n"
        message_text += f"👍 *Отзывы:*\n"
        message_text += f"   • Всего: {response['reviews']['total']}\n"
        message_text += f"   • За неделю: {response['reviews']['weekly']}\n\n"
        
        message_text += f"📝 *Объявления:*\n"
        
        message_text += f"👁 *Просмотры:* {response['statistics']['views']}\n"
        message_text += f"📲 *Контакты:* {response['statistics']['contacts']}\n"
        message_text += f"❤️ *В избранном:* {response['statistics']['favorites']}\n\n"
        
        message_text += f"💰 *Финансы:*\n"
        message_text += f"   • Реальный баланс: {response['balance_real']} ₽\n"
        message_text += f"   • Бонусы: {response['balance_bonus']} ₽\n"
        message_text += f"   • Аванс: {response['advance']} ₽\n\n"
        
        message_text += f"💸 *Расходы за неделю:* "
        
        # Добавляем расходы и детализацию
        expenses_message = format_expenses_message(response.get('expenses', {}))
        message_text += expenses_message

        # Отправляем отчет на указанный ID для недельных отчетов
        bot.send_message(telegram_id, message_text, parse_mode="Markdown")
        
    except AvitoAccount.DoesNotExist:
        logger.error(f"Аккаунт с ID {account_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке недельного отчета: {e}")

def add_avito_account(message):
    """Обработчик для добавления нового аккаунта Авито"""
    from bot.handlers.registration import add_avito_account as register_new_account
    register_new_account(message)
