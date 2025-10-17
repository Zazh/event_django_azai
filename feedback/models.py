from django.db import models


class FeedbackRequest(models.Model):
    """Заявки с сайта"""

    STATUS_CHOICES = [
        ('new', 'Новая'),
        ('in_progress', 'В работе'),
        ('completed', 'Завершена'),
        ('cancelled', 'Отменена'),
    ]

    full_name = models.CharField('ФИО', max_length=200)
    phone = models.CharField('Телефон', max_length=50)
    company = models.CharField('Компания', max_length=200)
    source = models.CharField('Источник', max_length=200, blank=True, help_text='Откуда пришла заявка')
    status = models.CharField('Статус', max_length=20, choices=STATUS_CHOICES, default='new')

    # Дополнительные поля
    comment = models.TextField('Комментарий администратора', blank=True)
    created_at = models.DateTimeField('Дата создания', auto_now_add=True)
    updated_at = models.DateTimeField('Дата обновления', auto_now=True)

    class Meta:
        verbose_name = 'Заявка'
        verbose_name_plural = 'Заявки'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.full_name} - {self.phone} ({self.get_status_display()})"