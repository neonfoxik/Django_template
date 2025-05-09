# Generated by Django 5.1.6 on 2025-04-27 18:09

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0004_remove_user_day_chats_remove_user_week_chats'),
    ]

    operations = [
        migrations.AddField(
            model_name='user',
            name='daily_expense',
            field=models.FloatField(default=0, verbose_name='Дневной расход'),
        ),
        migrations.AddField(
            model_name='user',
            name='last_balance',
            field=models.FloatField(default=0, verbose_name='Последний баланс'),
        ),
        migrations.AddField(
            model_name='user',
            name='last_balance_check',
            field=models.DateTimeField(blank=True, null=True, verbose_name='Время последней проверки баланса'),
        ),
        migrations.AddField(
            model_name='user',
            name='weekly_expense',
            field=models.FloatField(default=0, verbose_name='Недельный расход'),
        ),
    ]
