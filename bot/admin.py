from django.contrib import admin
from .models import User

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

admin.site.register(User, UserAdmin)
