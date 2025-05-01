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