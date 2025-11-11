from django.shortcuts import render


def service_list(request):
    """Список услуг (заглушка)"""
    return render(request, 'services/service_list.html', {})
