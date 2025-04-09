from django.db import models


class User(models.Model):
    telegram_id = models.BigIntegerField(unique=True, verbose_name='ID телеграм')
    user_name = models.CharField(max_length=100, blank=True, null=True, verbose_name='Имя пользователя')
    avito_api_key = models.CharField(max_length=255, blank=True, null=True, verbose_name='API ключ Авито')
    avito_client_id = models.CharField(max_length=255, blank=True, null=True, verbose_name='Client ID Авито')
    avito_client_secret = models.CharField(max_length=255, blank=True, null=True, verbose_name='Client Secret Авито')
    avito_token = models.TextField(blank=True, null=True, verbose_name='Авито токен')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='Дата создания')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='Дата обновления')

    class Meta:
        verbose_name = 'Пользователя'
        verbose_name_plural = 'Пользователи'

    def __str__(self):
        return f'Пользователь {self.user_name} - {self.telegram_id}'
