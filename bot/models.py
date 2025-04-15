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


class ItemData(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='item_data',
        verbose_name='Пользователь'
    )
    item_id = models.CharField(
        max_length=100,
        verbose_name='ID предмета'
    )
    view_price = models.FloatField(
        verbose_name='Цена за просмотр',
        default=0.0
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name='Дата обновления'
    )

    class Meta:
        unique_together = ('user', 'item_id')
        verbose_name = 'Данные предмета'
        verbose_name_plural = 'Данные предметов'
