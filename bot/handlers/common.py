from bot import bot
from bot.models import User, AvitoAccount, UserAvitoAccount, DailyReport, WeeklyReport
from bot.keyboards import main_markup
from bot.texts import MAIN_TEXT
from bot.statistics import get_daily_statistics, get_weekly_statistics
import telebot
from django.db import models
import datetime

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
        
        # Сохраняем отчет в базу данных
        save_daily_report_to_db(response, account)
        
        # Используем функцию форматирования отчета с процентными изменениями
        message_text = format_report_message_with_comparison(response, account, is_weekly=False)
        
        bot.send_message(chat_id, message_text)
        
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
        
        # Сохраняем отчет в базу данных
        save_weekly_report_to_db(response, account)
        
        # Используем функцию форматирования отчета с процентными изменениями
        message_text = format_report_message_with_comparison(response, account, is_weekly=True)
        
        bot.send_message(chat_id, message_text)
        
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

def format_report_message(response, account_name, is_weekly=False):
    """
    Форматирует отчет в структурированном виде.
    
    Args:
        response: Данные статистики
        account_name: Название аккаунта
        is_weekly: True для недельного отчета, False для дневного
        
    Returns:
        str: Форматированное сообщение отчета
    """
    # Определяем период для заголовка
    if is_weekly:
        title = f"Отчет за период: {response['period']}"
    else:
        title = f"Отчет за {response['date']}"
    
    # Показатели
    views = response['statistics']['views']
    contacts = response['statistics']['contacts']
    total_calls = response['calls']['total']
    missed_calls = response['calls']['missed']
    total_items = response['items']['total']
    
    # Расчет конверсии (если просмотры есть, иначе 0)
    conversion = (contacts / views * 100) if views > 0 else 0
    
    # Расходы
    total_expenses = response['expenses'].get('total', 0)
    
    # Стоимость контакта (если контакты есть, иначе 0)
    contact_cost = (total_expenses / contacts) if contacts > 0 else 0
    
    # Детализация расходов
    promo_expenses = 0
    xl_expenses = 0
    discount_expenses = 0
    
    for service, details in response['expenses'].get('details', {}).items():
        service_lower = service.lower()
        amount = details.get('amount', 0)
        
        if 'продвижение' in service_lower or 'promotion' in service_lower:
            promo_expenses += amount
        elif 'xl' in service_lower or 'выделение' in service_lower:
            xl_expenses += amount
        elif 'рассылка' in service_lower or 'скидка' in service_lower or 'discount' in service_lower:
            discount_expenses += amount
    
    # Работа менеджеров
    unanswered_messages = response['chats'].get('unanswered', 0)
    new_reviews = response['reviews'].get('today' if not is_weekly else 'weekly', 0)
    
    # Устанавливаем уровень сервиса 100% напрямую
    service_level = 100.0
    
    # Финансы
    balance_real = response['balance_real']
    advance = response['advance']
    
    # Формируем сообщение
    message = f"{title}\n\n"
    
    # Раздел показателей
    message += "Показатели\n"
    message += f"✔️Объявления: {total_items} шт\n"
    message += f"✔️Просмотры: {views}\n"
    message += f"✔️Контакты: {contacts}\n"
    message += f"✔️Конверсия в контакты: {conversion:.1f}%\n"
    message += f"✔️Стоимость контакта: {contact_cost:.0f} ₽\n"
    message += f"❗️Всего звонков: {total_calls}\n\n"
    
    # Раздел расходов
    message += "Расходы\n"
    message += f"Общие: {total_expenses:.0f} ₽\n"
    message += f"На продвижение: {promo_expenses:.0f} ₽\n"
    message += f"На XL и выделение: {xl_expenses:.0f} ₽\n"
    message += f"Рассылка скидок: {discount_expenses:.0f} ₽\n\n"
    
    # Раздел работы менеджеров
    message += "Работа менеджеров\n"
    message += f"Непринятые звонки: {missed_calls}\n"
    message += f"Сообщения без ответа: {unanswered_messages}\n"
    message += f"Уровень сервиса: {service_level:.0f}%\n"
    message += f"Новые отзывы: {new_reviews}\n\n"
    
    # Раздел финансов
    message += "—————————\n"
    message += f"CPA баланс: {advance:.0f} ₽\n"
    message += f"Кошелек: {balance_real:.0f} ₽\n"
    
    return message

def format_report_message_with_comparison(response, account, is_weekly=False):
    """
    Форматирует отчет с процентными изменениями по сравнению с предыдущим периодом.
    
    Args:
        response: Данные текущей статистики
        account: Объект аккаунта AvitoAccount
        is_weekly: True для недельного отчета, False для дневного
        
    Returns:
        str: Форматированное сообщение отчета с изменениями
    """
    # Получаем предыдущий отчет для сравнения
    if is_weekly:
        previous_report = WeeklyReport.objects.filter(
            avito_account=account
        ).order_by('-date').first()
    else:
        previous_report = DailyReport.objects.filter(
            avito_account=account
        ).order_by('-date').first()
    
    # Определяем период для заголовка
    if is_weekly:
        title = f"Отчет за период: {response['period']}"
    else:
        title = f"Отчет за {response['date']}"
    
    # Показатели текущего отчета
    views = response['statistics']['views']
    contacts = response['statistics']['contacts']
    total_calls = response['calls']['total']
    missed_calls = response['calls']['missed']
    total_items = response['items']['total']
    
    # Расчет конверсии (если просмотры есть, иначе 0)
    conversion = (contacts / views * 100) if views > 0 else 0
    
    # Расходы
    total_expenses = response['expenses'].get('total', 0)
    
    # Стоимость контакта (если контакты есть, иначе 0)
    contact_cost = (total_expenses / contacts) if contacts > 0 else 0
    
    # Детализация расходов
    promo_expenses = 0
    xl_expenses = 0
    discount_expenses = 0
    
    for service, details in response['expenses'].get('details', {}).items():
        service_lower = service.lower()
        amount = details.get('amount', 0)
        
        if 'продвижение' in service_lower or 'promotion' in service_lower:
            promo_expenses += amount
        elif 'xl' in service_lower or 'выделение' in service_lower:
            xl_expenses += amount
        elif 'рассылка' in service_lower or 'скидка' in service_lower or 'discount' in service_lower:
            discount_expenses += amount
    
    # Работа менеджеров
    unanswered_messages = response['chats'].get('unanswered', 0)
    new_reviews = response['reviews'].get('today' if not is_weekly else 'weekly', 0)
    
    # Устанавливаем уровень сервиса 100% напрямую
    service_level = 100.0
    
    # Финансы
    balance_real = response['balance_real']
    advance = response['advance']
    
    # Вычисляем процентные изменения, если есть предыдущий отчет
    if previous_report:
        # Показатели
        total_items_change = calculate_percentage_change(total_items, previous_report.total_items)
        views_change = calculate_percentage_change(views, previous_report.views)
        contacts_change = calculate_percentage_change(contacts, previous_report.contacts)
        conversion_change = calculate_percentage_change(conversion, previous_report.conversion_rate)
        contact_cost_change = calculate_percentage_change(contact_cost, previous_report.contact_cost)
        total_calls_change = calculate_percentage_change(total_calls, previous_report.total_calls)
        
        # Расходы
        total_expenses_change = calculate_percentage_change(total_expenses, previous_report.total_expenses)
        promo_expenses_change = calculate_percentage_change(promo_expenses, previous_report.promo_expenses)
        xl_expenses_change = calculate_percentage_change(xl_expenses, previous_report.xl_expenses)
        discount_expenses_change = calculate_percentage_change(discount_expenses, previous_report.discount_expenses)
        
        # Работа менеджеров
        missed_calls_change = calculate_percentage_change(missed_calls, previous_report.missed_calls)
        unanswered_messages_change = calculate_percentage_change(unanswered_messages, previous_report.unanswered_chats)
        service_level_change = calculate_percentage_change(service_level, previous_report.service_level)
        
        # Для поля new_reviews используем правильное название в зависимости от типа отчета
        if is_weekly:
            new_reviews_change = calculate_percentage_change(new_reviews, previous_report.weekly_reviews)
        else:
            new_reviews_change = calculate_percentage_change(new_reviews, previous_report.new_reviews)
    else:
        # Если нет предыдущего отчета, все изменения равны нулю
        total_items_change = views_change = contacts_change = conversion_change = 0
        contact_cost_change = total_calls_change = 0
        total_expenses_change = promo_expenses_change = xl_expenses_change = discount_expenses_change = 0
        missed_calls_change = unanswered_messages_change = service_level_change = new_reviews_change = 0
    
    # Формируем сообщение с изменениями
    message = f"{title}\n\n"
    
    # Раздел показателей с изменениями
    message += "Показатели\n"
    message += format_with_change("Объявления: " + str(total_items) + " шт", total_items_change)
    message += format_with_change("Просмотры: " + str(views), views_change)
    message += format_with_change("Контакты: " + str(contacts), contacts_change)
    message += format_with_change("Конверсия в контакты: " + f"{conversion:.1f}%", conversion_change)
    message += format_with_change("Стоимость контакта: " + f"{contact_cost:.0f} ₽", contact_cost_change)
    message += format_with_change("Всего звонков: " + str(total_calls), total_calls_change)
    message += "\n"
    
    # Раздел расходов с изменениями
    message += "Расходы\n"
    message += format_with_change("Общие: " + f"{total_expenses:.0f} ₽", total_expenses_change)
    message += format_with_change("На продвижение: " + f"{promo_expenses:.0f} ₽", promo_expenses_change)
    message += format_with_change("На XL и выделение: " + f"{xl_expenses:.0f} ₽", xl_expenses_change)
    message += format_with_change("Рассылка скидок: " + f"{discount_expenses:.0f} ₽", discount_expenses_change)
    message += "\n"
    
    # Раздел работы менеджеров с изменениями
    message += "Работа менеджеров\n"
    # Для пропущенных звонков и неотвеченных сообщений положительное изменение - это плохо, 
    # а отрицательное - хорошо, поэтому используем специальную функцию форматирования
    message += format_with_change_inverse("Непринятые звонки: " + str(missed_calls), missed_calls_change)
    message += format_with_change_inverse("Сообщения без ответа: " + str(unanswered_messages), unanswered_messages_change)
    message += format_with_change("Уровень сервиса: " + f"{service_level:.0f}%", service_level_change)
    message += format_with_change("Новые отзывы: " + str(new_reviews), new_reviews_change)
    message += "\n"
    
    # Раздел финансов (без изменений)
    message += "—————————\n"
    message += f"CPA баланс: {advance:.0f} ₽\n"
    message += f"Кошелек: {balance_real:.0f} ₽\n"
    
    return message

def format_with_change_inverse(text, change):
    """
    Форматирует строку с добавлением процентного изменения для метрик,
    где увеличение - это негативный тренд, а уменьшение - позитивный.
    
    Args:
        text: Основной текст строки
        change: Процентное изменение
        
    Returns:
        str: Отформатированная строка с изменением
    """
    # Определяем знак изменения и префикс - инвертируем логику
    prefix = ""
    if change < 0:  # Отрицательное изменение - хорошо
        prefix = "✔️ "
        change_text = f" ({change:.1f}%)"
    elif change > 0:  # Положительное изменение - плохо
        prefix = "❗️ "
        change_text = f" (+{change:.1f}%)"
    else:
        prefix = "✔️ "
        change_text = " (0%)"
    
    return f"{prefix}{text}{change_text}\n"

def calculate_percentage_change(current, previous):
    """
    Рассчитывает процентное изменение между текущим и предыдущим значением.
    
    Args:
        current: Текущее значение
        previous: Предыдущее значение
        
    Returns:
        float: Процентное изменение (положительное или отрицательное)
    """
    if previous == 0:
        return 0  # Избегаем деления на ноль
    return ((current - previous) / previous) * 100

def format_with_change(text, change):
    """
    Форматирует строку с добавлением процентного изменения.
    
    Args:
        text: Основной текст строки
        change: Процентное изменение
        
    Returns:
        str: Отформатированная строка с изменением
    """
    # Определяем знак изменения и префикс
    prefix = ""
    if change > 0:
        prefix = "✔️ "
        change_text = f" (+{change:.1f}%)"
    elif change < 0:
        prefix = "❗️ "
        change_text = f" ({change:.1f}%)"
    else:
        prefix = "✔️ "
        change_text = " (0%)"
    
    return f"{prefix}{text}{change_text}\n"

def send_daily_report(telegram_id, account_id):
    """Отправка дневного отчета по ID в Telegram и ID аккаунта Авито"""
    try:
        account = AvitoAccount.objects.get(id=account_id)
        client_id = account.client_id
        client_secret = account.client_secret
        response = get_daily_statistics(client_id, client_secret)
        
        # Сохраняем отчет в базу данных
        save_daily_report_to_db(response, account)
        
        # Используем функцию форматирования отчета с процентными изменениями
        message_text = format_report_message_with_comparison(response, account, is_weekly=False)

        # Отправляем отчет на указанный ID для дневных отчетов
        bot.send_message(telegram_id, message_text)
        
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
        
        # Сохраняем отчет в базу данных
        save_weekly_report_to_db(response, account)
        
        # Используем функцию форматирования отчета с процентными изменениями
        message_text = format_report_message_with_comparison(response, account, is_weekly=True)

        # Отправляем отчет на указанный ID для недельных отчетов
        bot.send_message(telegram_id, message_text)
        
    except AvitoAccount.DoesNotExist:
        logger.error(f"Аккаунт с ID {account_id} не найден")
    except Exception as e:
        logger.error(f"Ошибка при отправке недельного отчета: {e}")

def add_avito_account(message):
    """Обработчик для добавления нового аккаунта Авито"""
    from bot.handlers.registration import add_avito_account as register_new_account
    register_new_account(message)

def get_daily_reports_for_chat(chat_id):
    """Получение дневных отчетов для всех аккаунтов, связанных с чатом по daily_report_tg_id"""
    # Получаем все аккаунты с указанным ID чата для дневных отчетов
    accounts = AvitoAccount.objects.filter(
        models.Q(daily_report_tg_id=str(chat_id)) | models.Q(daily_report_tg_id=chat_id),
        client_id__isnull=False, 
        client_secret__isnull=False
    ).exclude(client_id="none").distinct()
    
    logger.info(f"ОТЛАДКА: Найдено аккаунтов Авито для дневных отчетов по chat_id={chat_id}: {accounts.count()}")
    
    if not accounts.exists():
        # В целях безопасности показываем сообщение только если чат привязан
        bot.send_message(chat_id, f"К данному чату (ID: {chat_id}) не прилинкован ни один авито аккаунт. Укажите этот ID в поле daily_report_tg_id авито аккаунта через админ панель.")
        return
    
    # Для каждого аккаунта получаем отчет
    for account in accounts:
        daily_report_for_account(chat_id, account.id)

def get_weekly_reports_for_chat(chat_id):
    """Получение недельных отчетов для всех аккаунтов, связанных с чатом по weekly_report_tg_id"""
    # Получаем все аккаунты с указанным ID чата для недельных отчетов
    accounts = AvitoAccount.objects.filter(
        models.Q(weekly_report_tg_id=str(chat_id)) | models.Q(weekly_report_tg_id=chat_id),
        client_id__isnull=False, 
        client_secret__isnull=False
    ).exclude(client_id="none").distinct()
    
    logger.info(f"ОТЛАДКА: Найдено аккаунтов Авито для недельных отчетов по chat_id={chat_id}: {accounts.count()}")
    
    if not accounts.exists():
        # В целях безопасности показываем сообщение только если чат привязан
        bot.send_message(chat_id, f"К данному чату (ID: {chat_id}) не прилинкован ни один авито аккаунт. Укажите этот ID в поле weekly_report_tg_id авито аккаунта через админ панель.")
        return
    
    # Для каждого аккаунта получаем отчет
    for account in accounts:
        weekly_report_for_account(chat_id, account.id)

def save_daily_report_to_db(response, account):
    """Сохраняет дневной отчет в базу данных"""
    try:
        # Получаем или создаем объект отчета за текущий день
        date_obj = datetime.datetime.strptime(response['date'], '%d.%m.%Y').date()
        logger.info(f"Сохраняем отчет за дату: {response['date']}, объект даты: {date_obj}")
        
        # Удаляем существующие отчеты за этот день для данного аккаунта
        deleted_count = DailyReport.objects.filter(avito_account=account, date=date_obj).delete()
        logger.info(f"Удалено существующих отчетов: {deleted_count}")
        
        # Создаем новый отчет
        daily_report = DailyReport(
            avito_account=account,
            date=date_obj,
            total_items=0,
            views=0,
            contacts=0,
            conversion_rate=0,
            contact_cost=0,
            total_calls=0,
            answered_calls=0,
            missed_calls=0,
            total_chats=0,
            new_chats=0,
            unanswered_chats=0,
            phones_received=0,
            rating=0,
            total_reviews=0,
            new_reviews=0,
            with_xl_promotion=0,
            favorites=0,
            total_expenses=0,
            promo_expenses=0,
            xl_expenses=0,
            discount_expenses=0,
            service_level=100,  # Устанавливаем уровень сервиса всегда 100
            balance_real=0,
            balance_bonus=0,
            advance=0
        )
        
        # Обновляем значения отчета
        calls = response.get('calls', {})
        chats = response.get('chats', {})
        statistics = response.get('statistics', {})
        items = response.get('items', {})
        reviews = response.get('reviews', {})
        expenses = response.get('expenses', {})
        expenses_details = expenses.get('details', {})
        
        # Расходы на продвижение
        promo_expenses = 0
        xl_expenses = 0
        discount_expenses = 0
        
        # Извлекаем данные из деталей расходов
        for key, value in expenses_details.items():
            if 'продвижен' in key.lower() or 'premium' in key.lower() or 'вип' in key.lower() or 'турбо' in key.lower() or 'быстр' in key.lower():
                promo_expenses += value.get('amount', 0)
            elif 'xl' in key.lower() or 'выделен' in key.lower():
                xl_expenses += value.get('amount', 0)
            elif 'скид' in key.lower() or 'discount' in key.lower():
                discount_expenses += value.get('amount', 0)
            
        # Общие расходы
        total_expenses = expenses.get('total', 0)
        
        # Обновляем значения из API
        daily_report.total_items = items.get('total', 0)
        daily_report.with_xl_promotion = items.get('with_xl_promotion', 0)
        daily_report.views = statistics.get('views', 0)
        daily_report.contacts = statistics.get('contacts', 0)
        
        # Расчет конверсии (если просмотры есть, иначе 0)
        if daily_report.views > 0:
            daily_report.conversion_rate = round(daily_report.contacts / daily_report.views * 100, 2)
        
        # Стоимость контакта (если контакты есть, иначе 0)
        if daily_report.contacts > 0:
            daily_report.contact_cost = round(total_expenses / daily_report.contacts, 2)
            
        # Звонки
        daily_report.total_calls = calls.get('total', 0)
        daily_report.answered_calls = calls.get('answered', 0)
        daily_report.missed_calls = calls.get('missed', 0)
        
        # Чаты
        daily_report.total_chats = chats.get('total', 0)
        daily_report.new_chats = chats.get('new', 0)
        
        # Показы телефонов
        daily_report.phones_received = response.get('phones_received', 0)
        
        # Рейтинг и отзывы
        daily_report.rating = response.get('rating', 0)
        daily_report.total_reviews = reviews.get('total', 0)
        daily_report.new_reviews = reviews.get('today', 0)
        daily_report.with_xl_promotion = items.get('with_xl_promotion', 0)
        daily_report.favorites = statistics.get('favorites', 0)
        daily_report.total_expenses = expenses.get('total', 0)
        daily_report.promo_expenses = promo_expenses
        daily_report.xl_expenses = xl_expenses
        daily_report.discount_expenses = discount_expenses
        daily_report.service_level = 100  # Устанавливаем уровень сервиса всегда 100
        daily_report.balance_real = response.get('balance_real', 0)
        daily_report.balance_bonus = response.get('balance_bonus', 0)
        daily_report.advance = response.get('advance', 0)
        
        daily_report.save()
        logger.info(f"Дневной отчет за {response['date']} сохранен в базу данных: ID={daily_report.id}")
        
        return daily_report
    except Exception as e:
        logger.error(f"Ошибка при сохранении дневного отчета в базу данных: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return None

def save_weekly_report_to_db(response, account):
    """Сохраняет недельный отчет в базу данных"""
    try:
        # Получаем дату начала и конца недели из строки периода
        if 'period' in response:
            period_parts = response['period'].split(' - ')
            start_date = datetime.datetime.strptime(period_parts[0], '%d.%m.%Y').date()
            end_date = datetime.datetime.strptime(period_parts[1], '%d.%m.%Y').date()
        else:
            # Если периода нет, берем текущую дату и дату 7 дней назад
            end_date = datetime.date.today()
            start_date = end_date - datetime.timedelta(days=7)
        
        # Удаляем существующие отчеты за эту неделю для данного аккаунта
        WeeklyReport.objects.filter(avito_account=account, date=end_date).delete()
        
        # Создаем новый отчет
        weekly_report = WeeklyReport(
            avito_account=account,
            date=end_date,
            period_start=start_date,
            period_end=end_date,
            total_items=0,
            views=0,
            contacts=0,
            conversion_rate=0,
            contact_cost=0,
            total_calls=0,
            answered_calls=0,
            missed_calls=0,
            total_chats=0,
            unanswered_chats=0,
            phones_received=0,
            rating=0,
            total_reviews=0,
            weekly_reviews=0,
            with_xl_promotion=0,
            favorites=0,
            total_expenses=0,
            promo_expenses=0,
            xl_expenses=0,
            discount_expenses=0,
            service_level=100,  # Устанавливаем уровень сервиса всегда 100
            balance_real=0,
            balance_bonus=0,
            advance=0
        )
        
        # Обновляем значения отчета
        calls = response.get('calls', {})
        chats = response.get('chats', {})
        statistics = response.get('statistics', {})
        items = response.get('items', {})
        reviews = response.get('reviews', {})
        expenses = response.get('expenses', {})
        expenses_details = expenses.get('details', {})
        
        # Расходы на продвижение
        promo_expenses = 0
        xl_expenses = 0
        discount_expenses = 0
        
        # Обрабатываем детали расходов
        for service_type, service_data in expenses_details.items():
            amount = service_data.get('amount', 0)
            # Классифицируем расходы по типу услуги
            if 'продвижение' in service_type.lower() or 'bbip' in service_type.lower():
                promo_expenses += amount
            elif 'xl' in service_type.lower() or 'vas' in service_type.lower():
                xl_expenses += amount
            elif 'скид' in service_type.lower() or 'discount' in service_type.lower():
                discount_expenses += amount
        
        # Основные показатели
        views = statistics.get('views', 0)
        contacts = statistics.get('contacts', 0)
        
        # Рассчитываем конверсию
        conversion_rate = 0
        if views > 0:
            conversion_rate = (contacts / views) * 100
        
        # Рассчитываем стоимость контакта
        contact_cost = 0
        if contacts > 0:
            contact_cost = expenses.get('total', 0) / contacts
        
        # Обновляем существующий отчет
        weekly_report.total_items = items.get('total', 0)
        weekly_report.views = views
        weekly_report.contacts = contacts
        weekly_report.conversion_rate = conversion_rate
        weekly_report.contact_cost = contact_cost
        weekly_report.total_calls = calls.get('total', 0)
        weekly_report.answered_calls = calls.get('answered', 0)
        weekly_report.missed_calls = calls.get('missed', 0)
        weekly_report.total_chats = chats.get('total', 0)
        weekly_report.unanswered_chats = chats.get('unanswered', 0)
        weekly_report.phones_received = response.get('phones_received', 0)
        weekly_report.rating = response.get('rating', 0)
        weekly_report.total_reviews = reviews.get('total', 0)
        weekly_report.weekly_reviews = reviews.get('weekly', 0)
        weekly_report.with_xl_promotion = items.get('with_xl_promotion', 0)
        weekly_report.favorites = statistics.get('favorites', 0)
        weekly_report.total_expenses = expenses.get('total', 0)
        weekly_report.promo_expenses = promo_expenses
        weekly_report.xl_expenses = xl_expenses
        weekly_report.discount_expenses = discount_expenses
        weekly_report.service_level = 100  # Устанавливаем уровень сервиса всегда 100
        weekly_report.balance_real = response.get('balance_real', 0)
        weekly_report.balance_bonus = response.get('balance_bonus', 0)
        weekly_report.advance = response.get('advance', 0)
        
        weekly_report.save()
        logger.info(f"Недельный отчет за период {start_date} - {end_date} сохранен в базу данных")
        
        return weekly_report
    except Exception as e:
        logger.error(f"Ошибка при сохранении недельного отчета в базу данных: {e}")
        return None
