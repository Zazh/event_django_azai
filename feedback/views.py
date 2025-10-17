from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods
import json
from .models import FeedbackRequest
from .telegram import send_telegram_notification
import logging

logger = logging.getLogger(__name__)


@csrf_exempt
@require_http_methods(["POST"])
def submit_feedback(request):
    """API endpoint для приема заявок"""
    try:
        data = json.loads(request.body)

        # Валидация обязательных полей
        required_fields = ['full_name', 'phone', 'company']
        for field in required_fields:
            if not data.get(field):
                return JsonResponse({
                    'success': False,
                    'error': f'Поле {field} обязательно для заполнения'
                }, status=400)

        # Создаем заявку
        feedback = FeedbackRequest.objects.create(
            full_name=data.get('full_name'),
            phone=data.get('phone'),
            company=data.get('company'),
            source=data.get('source', 'Неизвестно')
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