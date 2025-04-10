# Generated by Django 5.1.6 on 2025-04-09 12:32

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('telegram_id', models.CharField(max_length=50, primary_key=True, serialize=False)),
                ('user_name', models.CharField(max_length=35, verbose_name='Имя')),
                ('avito_api_key', models.CharField(blank=True, default='none', max_length=50, null=True, verbose_name='секретный авито токен')),
            ],
            options={
                'verbose_name': 'Пользователь',
                'verbose_name_plural': 'Пользователи',
            },
        ),
    ]
