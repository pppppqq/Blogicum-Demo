from django.shortcuts import render
from django.views.generic import TemplateView


class About(TemplateView):
    """
    Представление для отображения страницы с информацией
    о проекте.
    """

    template_name = 'pages/about.html'


class Rules(TemplateView):
    """Представление для отображения страницы с правилами."""

    template_name = 'pages/rules.html'


def page_not_found(request, exception):
    """Обработчик для отображения страницы ошибки 404 (Не найдено)."""
    return render(request, 'pages/404.html', status=404)


def csrf_failure(request, reason=''):
    """Обработчик для отображения страницы ошибки 403."""
    return render(request, 'pages/403csrf.html', status=403)


def server_error(request):
    """Обработчик для отображения страницы ошибки 500."""
    return render(request, 'pages/500.html', status=500)
