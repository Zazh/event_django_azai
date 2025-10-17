import requests
from django.conf import settings
import logging
import html

logger = logging.getLogger(__name__)


def escape_html(text):
    """Экранирует HTML символы для Telegram"""
    if not text:
        return ""
    return html.escape(str(text))


def send_telegram_notification(feedback):
    """
    Отправляет уведомление о новой заявке в Telegram

    :param feedback: экземпляр модели FeedbackRequest
    :return: True если успешно, False если ошибка
    """
    bot_token = settings.TELEGRAM_BOT_TOKEN
    chat_id = settings.TELEGRAM_CHAT_ID

    # Проверяем наличие настроек
    if not bot_token or not chat_id:
        logger.warning('Telegram settings not configured')
        return False

    # Экранируем данные для HTML
    full_name = escape_html(feedback.full_name)
    phone = escape_html(feedback.phone)
    company = escape_html(feedback.company)
    source = escape_html(feedback.source)
    date_str = feedback.created_at.strftime('%d.%m.%Y %H:%M')

    # Формируем сообщение
    message = f"""
🔔 <b>Новая заявка с сайта!</b>

👤 <b>ФИО:</b> {full_name}
📱 <b>Телефон:</b> {phone}
🏢 <b>Компания:</b> {company}
📍 <b>Источник:</b> {source}
🕐 <b>Дата:</b> {date_str}

ID заявки: #{feedback.id}
    """.strip()

    # Отправляем через Telegram Bot API
    url = f'https://api.telegram.org/bot{bot_token}/sendMessage'

    data = {
        'chat_id': chat_id,
        'text': message,
        'parse_mode': 'HTML'
    }

    try:
        response = requests.post(url, data=data, timeout=10)

        # Выводим детали ошибки если есть
        if not response.ok:
            logger.error(f'Telegram API error: {response.status_code} - {response.text}')
            return False

        result = response.json()

        if result.get('ok'):
            logger.info(f'Telegram notification sent for feedback #{feedback.id}')
            return True
        else:
            logger.error(f'Telegram API error: {result}')
            return False

    except requests.exceptions.RequestException as e:
        logger.error(f'Failed to send Telegram notification: {str(e)}')
        return False