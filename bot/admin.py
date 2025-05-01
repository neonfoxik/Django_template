from django.contrib import admin
from .models import User, AvitoAccount, UserAvitoAccount

class UserAdmin(admin.ModelAdmin):
    list_display = ('user_name',)  # Удалены недопустимые поля
    search_fields = ('user_name',)
    ordering = ('-telegram_id',)  # Изменено на существующее поле

    def get_queryset(self, request):
        """Переопределяем метод для обработки ошибок при получении пользователей."""
        try:
            return super().get_queryset(request)
        except Exception as e:
            return User.objects.none()

class AvitoAccountAdmin(admin.ModelAdmin):
    list_display = ('name', 'client_id', 'last_balance', 'daily_expense', 'weekly_expense')
    search_fields = ('name',)
    list_filter = ('name',)

class UserAvitoAccountAdmin(admin.ModelAdmin):
    list_display = ('user', 'avito_account')
    search_fields = ('user__user_name', 'avito_account__name')
    list_filter = ('avito_account',)

admin.site.register(User, UserAdmin)
admin.site.register(AvitoAccount, AvitoAccountAdmin)
admin.site.register(UserAvitoAccount, UserAvitoAccountAdmin)
