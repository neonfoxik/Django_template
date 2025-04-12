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
    
    @property
    def current_balance(self):
        """Получение текущего баланса пользователя"""
        try:
            latest_balance = self.balance_records.order_by('-date').first()
            return latest_balance.amount if latest_balance else 0
        except:
            return 0
    
    @property
    def previous_balance(self):
        """Получение баланса пользователя за предыдущий день"""
        try:
            yesterday = datetime.date.today() - datetime.timedelta(days=1)
            prev_balance = self.balance_records.filter(date=yesterday).first()
            return prev_balance.amount if prev_balance else 0
        except:
            return 0
    
    @property
    def daily_expenses(self):
        """Расчет расходов за день"""
        try:
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            
            today_record = self.balance_records.filter(date=today).first()
            yesterday_record = self.balance_records.filter(date=yesterday).first()
            
            if not yesterday_record or not today_record:
                return 0
            
            # Если баланс вырос, значит пополнение, расход 0
            if today_record.amount > yesterday_record.amount:
                return 0
            
            # Иначе расходы - это разница между вчерашним и сегодняшним балансом
            return yesterday_record.amount - today_record.amount
        except:
            return 0
    
    @property
    def daily_deposit(self):
        """Расчет пополнений за день"""
        try:
            today = datetime.date.today()
            yesterday = today - datetime.timedelta(days=1)
            
            today_record = self.balance_records.filter(date=today).first()
            yesterday_record = self.balance_records.filter(date=yesterday).first()
            
            if not yesterday_record or not today_record:
                return 0
            
            # Если баланс вырос, значит было пополнение
            if today_record.amount > yesterday_record.amount:
                return today_record.amount - yesterday_record.amount
            
            # Иначе пополнения не было
            return 0
        except:
            return 0

    def __str__(self):
        return str(self.user_name)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'


class UserBalance(models.Model):
    """Модель для хранения ежедневного баланса пользователя"""
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='balance_records',
        verbose_name='Пользователь'
    )
    date = models.DateField(
        verbose_name='Дата',
        default=datetime.date.today
    )
    amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        verbose_name='Сумма баланса',
        default=0
    )
    
    class Meta:
        verbose_name = 'Баланс пользователя'
        verbose_name_plural = 'Балансы пользователей'
        # Уникальность записи по пользователю и дате
        unique_together = ('user', 'date')
        
    def __str__(self):
        return f"{self.user.user_name} - {self.date} - {self.amount} ₽"
