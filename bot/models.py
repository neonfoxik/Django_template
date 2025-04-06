from django.db import models


class User(models.Model):
    telegram_id = models.CharField(
        primary_key=True,
        max_length=50
    )
    user_name = models.CharField(
        max_length=35,
        verbose_name='Имя',
    )
    avito_api_key = models.CharField(
        max_length=50,
        verbose_name='секретный авито токен',
        null=True,
        blank=True,
        default="none",
    )

    def __str__(self):
        return str(self.user_name)

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
