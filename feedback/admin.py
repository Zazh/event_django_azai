from django.contrib import admin
from .models import FeedbackRequest


@admin.register(FeedbackRequest)
class FeedbackRequestAdmin(admin.ModelAdmin):
    list_display = ['full_name', 'phone', 'company', 'source', 'status', 'created_at']
    list_filter = ['status', 'created_at', 'source']
    search_fields = ['full_name', 'phone', 'company']
    list_editable = ['status']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Информация о клиенте', {
            'fields': ('full_name', 'phone', 'company', 'source')
        }),
        ('Статус и комментарии', {
            'fields': ('status', 'comment')
        }),
        ('Системная информация', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def has_delete_permission(self, request, obj=None):
        # Запрещаем удаление заявок
        return False