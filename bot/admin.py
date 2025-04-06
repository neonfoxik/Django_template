from django.contrib import admin
from .models import User, Goods, Events  # Добавлено Events

class UserAdmin(admin.ModelAdmin):
    list_display = ('user_tg_name', 'user_name', 'coins', 'last_farm', 'is_admin')
    search_fields = ('user_name', 'user_tg_name')
    list_filter = ('is_admin',)
    ordering = ('-coins',)

    def get_queryset(self, request):
        """Переопределяем метод для обработки ошибок при получении пользователей."""
        try:
            return super().get_queryset(request)
        except Exception as e:
            return User.objects.none()

class GoodsAdmin(admin.ModelAdmin):
    list_display = ('goods_name', 'goods_price')  # Поля для отображения в админке
    list_editable = ('goods_price',)
    search_fields = ('goods_name',)  # Поля для поиска
    ordering = ('goods_price',)  # Сортировка по цене

class EventsAdmin(admin.ModelAdmin):
    list_display = ('name', 'chanel_name', 'price', 'remaining_number_of_clicks')  # Поля для отображения в админке
    search_fields = ('name', 'chanel_name')  # Поля для поиска
    ordering = ('price',)  # Сортировка по цене

admin.site.register(User, UserAdmin)
admin.site.register(Goods, GoodsAdmin)  # Регистрация модели Goods с админкой
admin.site.register(Events, EventsAdmin)  # Регистрация модели Events с админкой
