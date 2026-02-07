"""
Интеграционный тест: экспорт статистики (CSV/HTML для PDF).
Запуск: из папки greenquality выполнить
  python manage.py test tests.test_export
"""
from django.test import TestCase, Client
from django.urls import reverse

from airline.models import Account, Role


class ExportStatisticsTest(TestCase):
    """Интеграционный тест: экспорт статистики для менеджера (CSV и PDF/HTML)."""

    def setUp(self):
        self.client = Client()
        self.role_manager = Role.objects.create(role_name='MANAGER')
        self.account_manager = Account.objects.create(
            email='manager@test.local',
            password='hashed',
            role_id=self.role_manager
        )

    def test_export_statistics(self):
        """Экспорт статистики: без логина редирект; под менеджером — CSV и HTML (PDF)."""
        # Без авторизации — редирект на логин
        url_csv = reverse('export_statistics', kwargs={'format_type': 'csv'})
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 302)
        self.assertIn('login', response.url)

        # Авторизация под менеджером
        session = self.client.session
        session['account_id'] = self.account_manager.id_account
        session.save()

        # CSV: статус 200, content-type csv, ожидаемые заголовки в теле
        response = self.client.get(url_csv)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.get('Content-Type', '').split(';')[0].strip(),
            'text/csv'
        )
        content = response.content.decode('utf-8-sig')
        self.assertIn('Статистика по статусам билетов', content)
        self.assertIn('Выручка по месяцам', content)

        # PDF (HTML для печати): статус 200, content-type html, вложение statistics.html
        url_pdf = reverse('export_statistics', kwargs={'format_type': 'pdf'})
        response = self.client.get(url_pdf)
        self.assertEqual(response.status_code, 200)
        self.assertIn('text/html', response.get('Content-Type', ''))
        self.assertIn('statistics.html', response.get('Content-Disposition', ''))
