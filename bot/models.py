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