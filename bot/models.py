from django.db import models
import datetime


class User(models.Model):
    telegram_id = models.CharField(
        primary_key=True,
        max_length=50
    )
    user_name = models.CharField(
        max_length=35,
        verbose_name='Имя',
    )
    
    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return self.user_name


class AvitoAccount(models.Model):
    name = models.CharField(
        max_length=100,
        verbose_name='Имя аккаунта',
    )
    client_id = models.CharField(
        max_length=50,
        verbose_name='Client ID Авито',
        null=True,
        blank=True,
        default="none",
    )
    client_secret = models.CharField(
        max_length=100,
        verbose_name='Client Secret Авито',
        null=True,
        blank=True,
        default="none",
    )
    daily_report_tg_id = models.CharField(
        max_length=50,
        verbose_name='Telegram ID для дневных отчетов',
        null=True,
        blank=True,
    )
    weekly_report_tg_id = models.CharField(
        max_length=50,
        verbose_name='Telegram ID для недельных отчетов',
        null=True,
        blank=True,
    )
    # Добавляем поля для отслеживания расходов
    daily_expense = models.FloatField(
        verbose_name='Дневной расход',
        default=0,
    )
    weekly_expense = models.FloatField(
        verbose_name='Недельный расход',
        default=0,
    )
    last_balance = models.FloatField(
        verbose_name='Последний баланс',
        default=0,
    )
    last_balance_check = models.DateTimeField(
        verbose_name='Время последней проверки баланса',
        null=True,
        blank=True,
    )
    
    class Meta:
        verbose_name = 'Аккаунт Авито'
        verbose_name_plural = 'Аккаунты Авито'
    
    def __str__(self):
        return self.name
    
    
class UserAvitoAccount(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='avito_accounts',
        verbose_name='Пользователь'
    )
    avito_account = models.ForeignKey(
        AvitoAccount,
        on_delete=models.CASCADE,
        related_name='users',
        verbose_name='Аккаунт Авито'
    )
    
    class Meta:
        verbose_name = 'Связь пользователь-аккаунт'
        verbose_name_plural = 'Связи пользователей и аккаунтов'
        unique_together = ('user', 'avito_account')
        
    def __str__(self):
        return f"{self.user.user_name} - {self.avito_account.name}"


class DailyReport(models.Model):
    avito_account = models.ForeignKey(
        AvitoAccount,
        on_delete=models.CASCADE,
        related_name='daily_reports',
        verbose_name='Аккаунт Авито'
    )
    date = models.DateField(
        verbose_name='Дата отчета',
        auto_now_add=True
    )
    # Показатели
    total_items = models.IntegerField(
        verbose_name='Всего объявлений',
        default=0
    )
    views = models.IntegerField(
        verbose_name='Просмотры',
        default=0
    )
    contacts = models.IntegerField(
        verbose_name='Контакты',
        default=0
    )
    conversion_rate = models.FloatField(
        verbose_name='Конверсия в контакты (%)',
        default=0
    )
    contact_cost = models.FloatField(
        verbose_name='Стоимость контакта',
        default=0
    )
    total_calls = models.IntegerField(
        verbose_name='Всего звонков',
        default=0
    )
    answered_calls = models.IntegerField(
        verbose_name='Отвеченные звонки',
        default=0
    )
    missed_calls = models.IntegerField(
        verbose_name='Пропущенные звонки',
        default=0
    )
    # Чаты
    total_chats = models.IntegerField(
        verbose_name='Всего чатов',
        default=0
    )
    new_chats = models.IntegerField(
        verbose_name='Новые чаты',
        default=0
    )
    unanswered_chats = models.IntegerField(
        verbose_name='Неотвеченные чаты',
        default=0
    )
    # Телефоны
    phones_received = models.IntegerField(
        verbose_name='Показы телефона',
        default=0
    )
    # Рейтинг и отзывы
    rating = models.FloatField(
        verbose_name='Рейтинг',
        default=0
    )
    total_reviews = models.IntegerField(
        verbose_name='Всего отзывов',
        default=0
    )
    new_reviews = models.IntegerField(
        verbose_name='Новые отзывы',
        default=0
    )
    # Объявления
    with_xl_promotion = models.IntegerField(
        verbose_name='Объявлений с XL-продвижением',
        default=0
    )
    # Статистика
    favorites = models.IntegerField(
        verbose_name='Добавлено в избранное',
        default=0
    )
    # Расходы
    total_expenses = models.FloatField(
        verbose_name='Общие расходы',
        default=0
    )
    promo_expenses = models.FloatField(
        verbose_name='Расходы на продвижение',
        default=0
    )
    xl_expenses = models.FloatField(
        verbose_name='Расходы на XL и выделение',
        default=0
    )
    discount_expenses = models.FloatField(
        verbose_name='Расходы на рассылку скидок',
        default=0
    )
    # Работа менеджеров
    service_level = models.FloatField(
        verbose_name='Уровень сервиса (%)',
        default=0
    )
    # Финансы
    balance_real = models.FloatField(
        verbose_name='Баланс кошелька',
        default=0
    )
    balance_bonus = models.FloatField(
        verbose_name='Бонусный баланс',
        default=0
    )
    advance = models.FloatField(
        verbose_name='CPA баланс',
        default=0
    )
    
    class Meta:
        verbose_name = 'Дневной отчет'
        verbose_name_plural = 'Дневные отчеты'
        ordering = ['-date']
    
    def __str__(self):
        return f"Дневной отчет для {self.avito_account.name} - {self.date}"


class WeeklyReport(models.Model):
    avito_account = models.ForeignKey(
        AvitoAccount,
        on_delete=models.CASCADE,
        related_name='weekly_reports',
        verbose_name='Аккаунт Авито'
    )
    date = models.DateField(
        verbose_name='Дата отчета',
        auto_now_add=True
    )
    period_start = models.DateField(
        verbose_name='Начало периода',
        null=True,
        blank=True
    )
    period_end = models.DateField(
        verbose_name='Конец периода',
        null=True, 
        blank=True
    )
    # Показатели
    total_items = models.IntegerField(
        verbose_name='Всего объявлений',
        default=0
    )
    views = models.IntegerField(
        verbose_name='Просмотры',
        default=0
    )
    contacts = models.IntegerField(
        verbose_name='Контакты',
        default=0
    )
    conversion_rate = models.FloatField(
        verbose_name='Конверсия в контакты (%)',
        default=0
    )
    contact_cost = models.FloatField(
        verbose_name='Стоимость контакта',
        default=0
    )
    total_calls = models.IntegerField(
        verbose_name='Всего звонков',
        default=0
    )
    answered_calls = models.IntegerField(
        verbose_name='Отвеченные звонки',
        default=0
    )
    missed_calls = models.IntegerField(
        verbose_name='Пропущенные звонки',
        default=0
    )
    # Чаты
    total_chats = models.IntegerField(
        verbose_name='Всего чатов',
        default=0
    )
    unanswered_chats = models.IntegerField(
        verbose_name='Неотвеченные чаты',
        default=0
    )
    # Телефоны
    phones_received = models.IntegerField(
        verbose_name='Показы телефона',
        default=0
    )
    # Рейтинг и отзывы
    rating = models.FloatField(
        verbose_name='Рейтинг',
        default=0
    )
    total_reviews = models.IntegerField(
        verbose_name='Всего отзывов',
        default=0
    )
    weekly_reviews = models.IntegerField(
        verbose_name='Новые отзывы за неделю',
        default=0
    )
    # Объявления
    with_xl_promotion = models.IntegerField(
        verbose_name='Объявлений с XL-продвижением',
        default=0
    )
    # Статистика
    favorites = models.IntegerField(
        verbose_name='Добавлено в избранное',
        default=0
    )
    # Расходы
    total_expenses = models.FloatField(
        verbose_name='Общие расходы',
        default=0
    )
    promo_expenses = models.FloatField(
        verbose_name='Расходы на продвижение',
        default=0
    )
    xl_expenses = models.FloatField(
        verbose_name='Расходы на XL и выделение',
        default=0
    )
    discount_expenses = models.FloatField(
        verbose_name='Расходы на рассылку скидок',
        default=0
    )
    # Работа менеджеров
    service_level = models.FloatField(
        verbose_name='Уровень сервиса (%)',
        default=0
    )
    # Финансы
    balance_real = models.FloatField(
        verbose_name='Баланс кошелька',
        default=0
    )
    balance_bonus = models.FloatField(
        verbose_name='Бонусный баланс',
        default=0
    )
    advance = models.FloatField(
        verbose_name='CPA баланс',
        default=0
    )
    
    class Meta:
        verbose_name = 'Недельный отчет'
        verbose_name_plural = 'Недельные отчеты'
        ordering = ['-date']
    
    def __str__(self):
        return f"Недельный отчет для {self.avito_account.name} - {self.date}"