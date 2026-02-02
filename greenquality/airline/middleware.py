"""
Middleware для подмены любой страницы 404 на нашу шаблонную (даже при DEBUG=True).
"""
from django.shortcuts import render


class Custom404Middleware:
    """
    Перехватывает любой ответ 404 и подменяет его нашей страницей 404.html.
    Так кастомная 404 показывается и при DEBUG=True (когда Django не вызывает handler404).
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        if response.status_code == 404:
            return render(request, '404.html', status=404)
        return response
