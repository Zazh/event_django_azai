from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import FeedbackRequest
from .telegram import send_telegram_notification
import logging

logger = logging.getLogger(__name__)

# Обязательные поля заявки и сообщение, если поле пустое
REQUIRED_FIELDS = (
    ('full_name', 'Укажите ФИО'),
    ('phone', 'Укажите телефон'),
)
COMPANY_PLACEHOLDER = 'Не указано'


def _text(data, key):
    """Значение поля заявки: без пробелов по краям, не длиннее поля модели; не строка — ''."""
    value = data.get(key)
    if not isinstance(value, str):
        return ''
    return value.strip()[:FeedbackRequest._meta.get_field(key).max_length]


@csrf_exempt
@require_http_methods(["POST"])
def submit_feedback(request):
    """API endpoint для приема заявок"""
    try:
        data = json.loads(request.body)
        if not isinstance(data, dict):
            return JsonResponse({
                'success': False,
                'error': 'Неверный формат данных'
            }, status=400)

        # Валидация обязательных полей (пробелы считаются пустым значением)
        for field, message in REQUIRED_FIELDS:
            if not _text(data, field):
                return JsonResponse({
                    'success': False,
                    'error': message
                }, status=400)

        # Создаем заявку; компания необязательна — правило одно для всех форм сайта
        feedback = FeedbackRequest.objects.create(
            full_name=_text(data, 'full_name'),
            phone=_text(data, 'phone'),
            company=_text(data, 'company') or COMPANY_PLACEHOLDER,
            source=_text(data, 'source') or 'Неизвестно'
        )

        # Отправляем в Telegram
        telegram_sent = send_telegram_notification(feedback)

        if telegram_sent:
            logger.info(f'Feedback #{feedback.id} sent to Telegram successfully')
        else:
            logger.warning(f'Feedback #{feedback.id} created but Telegram notification failed')

        return JsonResponse({
            'success': True,
            'message': 'Заявка успешно отправлена!',
            'id': feedback.id,
            'telegram_sent': telegram_sent
        })

    except json.JSONDecodeError:
        return JsonResponse({
            'success': False,
            'error': 'Неверный формат данных'
        }, status=400)

    except Exception as e:
        logger.error(f'Error processing feedback: {str(e)}')
        return JsonResponse({
            'success': False,
            'error': 'Внутренняя ошибка сервера'
        }, status=500)