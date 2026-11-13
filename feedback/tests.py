import json
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from .models import FeedbackRequest


class SubmitFeedbackTests(TestCase):
    """API заявок. Отправка в Telegram замокана во всех тестах — сеть не трогаем."""

    url = reverse('feedback:submit')

    def setUp(self):
        patcher = patch('feedback.views.send_telegram_notification', return_value=True)
        self.send_telegram = patcher.start()
        self.addCleanup(patcher.stop)

    def post(self, payload):
        return self.client.post(self.url, data=json.dumps(payload), content_type='application/json')

    def assert_rejected(self, response, message):
        self.assertEqual(response.status_code, 400)
        body = response.json()
        self.assertFalse(body['success'])
        self.assertEqual(body['error'], message)
        self.assertEqual(FeedbackRequest.objects.count(), 0)
        self.send_telegram.assert_not_called()

    def test_missing_full_name(self):
        response = self.post({'phone': '+7 701 000 0000', 'company': 'ТОО'})
        self.assert_rejected(response, 'Укажите ФИО')
        self.assertNotIn('full_name', response.json()['error'])

    def test_blank_full_name(self):
        self.assert_rejected(self.post({'full_name': '   ', 'phone': '+7 701 000 0000'}), 'Укажите ФИО')

    def test_missing_phone(self):
        response = self.post({'full_name': 'Айгерим', 'company': 'ТОО'})
        self.assert_rejected(response, 'Укажите телефон')
        self.assertNotIn('phone', response.json()['error'])

    def test_missing_company_saved_as_placeholder(self):
        response = self.post({'full_name': 'Айгерим', 'phone': '+7 701 000 0000'})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FeedbackRequest.objects.get().company, 'Не указано')

    def test_blank_company_saved_as_placeholder(self):
        response = self.post({'full_name': 'Айгерим', 'phone': '+7 701 000 0000', 'company': '   '})
        self.assertEqual(response.status_code, 200)
        self.assertEqual(FeedbackRequest.objects.get().company, 'Не указано')

    def test_full_payload(self):
        response = self.post({
            'full_name': ' Айгерим ', 'phone': '+7 701 000 0000',
            'company': 'ТОО «Ромашка»', 'source': 'Получить презентацию - LEGENDS',
        })
        self.assertEqual(response.status_code, 200)
        body = response.json()
        self.assertTrue(body['success'])
        self.assertTrue(body['telegram_sent'])
        feedback = FeedbackRequest.objects.get()
        self.assertEqual(body['id'], feedback.id)
        self.assertEqual(feedback.full_name, 'Айгерим')
        self.assertEqual(feedback.company, 'ТОО «Ромашка»')
        self.assertEqual(feedback.source, 'Получить презентацию - LEGENDS')
        self.send_telegram.assert_called_once_with(feedback)

    def test_telegram_failure_still_succeeds(self):
        self.send_telegram.return_value = False
        response = self.post({'full_name': 'Айгерим', 'phone': '+7 701 000 0000'})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()['success'])
        self.assertFalse(response.json()['telegram_sent'])
        self.assertEqual(FeedbackRequest.objects.count(), 1)

    def test_invalid_json(self):
        response = self.client.post(self.url, data='не json', content_type='application/json')
        self.assert_rejected(response, 'Неверный формат данных')

    def test_json_not_object(self):
        self.assert_rejected(self.post(['full_name']), 'Неверный формат данных')

    def test_get_not_allowed(self):
        self.assertEqual(self.client.get(self.url).status_code, 405)
