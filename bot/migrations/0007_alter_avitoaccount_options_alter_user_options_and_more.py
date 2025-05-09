# Generated by Django 5.1.6 on 2025-05-06 16:00

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('bot', '0006_avitoaccount_remove_user_client_id_and_more'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='avitoaccount',
            options={'verbose_name': 'Аккаунт Авито', 'verbose_name_plural': 'Аккаунты Авито'},
        ),
        migrations.AlterModelOptions(
            name='user',
            options={'verbose_name': 'Пользователь', 'verbose_name_plural': 'Пользователи'},
        ),
        migrations.CreateModel(
            name='AvitoAccountDailyStats',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('date', models.DateField(verbose_name='Дата статистики')),
                ('total_calls', models.IntegerField(default=0, verbose_name='Всего звонков')),
                ('answered_calls', models.IntegerField(default=0, verbose_name='Отвеченные звонки')),
                ('missed_calls', models.IntegerField(default=0, verbose_name='Пропущенные звонки')),
                ('total_chats', models.IntegerField(default=0, verbose_name='Всего чатов')),
                ('new_chats', models.IntegerField(default=0, verbose_name='Новые чаты')),
                ('phones_received', models.IntegerField(default=0, verbose_name='Показы телефона')),
                ('rating', models.FloatField(default=0, verbose_name='Рейтинг')),
                ('total_reviews', models.IntegerField(default=0, verbose_name='Всего отзывов')),
                ('daily_reviews', models.IntegerField(default=0, verbose_name='Отзывы за день')),
                ('total_items', models.IntegerField(default=0, verbose_name='Всего объявлений')),
                ('xl_promotion_count', models.IntegerField(default=0, verbose_name='Объявления с XL продвижением')),
                ('views', models.IntegerField(default=0, verbose_name='Просмотры')),
                ('contacts', models.IntegerField(default=0, verbose_name='Контакты')),
                ('favorites', models.IntegerField(default=0, verbose_name='В избранном')),
                ('balance_real', models.FloatField(default=0, verbose_name='Реальный баланс')),
                ('balance_bonus', models.FloatField(default=0, verbose_name='Бонусы')),
                ('advance', models.FloatField(default=0, verbose_name='Аванс')),
                ('daily_expense', models.FloatField(default=0, verbose_name='Расход за день')),
                ('expenses_details', models.TextField(blank=True, null=True, verbose_name='Детализация расходов JSON')),
                ('avito_account', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_stats', to='bot.avitoaccount', verbose_name='Аккаунт Авито')),
            ],
            options={
                'verbose_name': 'Ежедневная статистика аккаунта',
                'verbose_name_plural': 'Ежедневная статистика аккаунтов',
                'ordering': ['-date'],
                'unique_together': {('avito_account', 'date')},
            },
        ),
    ]
