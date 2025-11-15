# users/middleware.py
from django.shortcuts import redirect
from django.contrib import messages
from django.urls import reverse
from django.utils import timezone


class BanCheckMiddleware:
    """
    Middleware для проверки, не забанен ли пользователь.
    Блокирует доступ к сайту для забаненных пользователей.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Пути, которые доступны даже забаненным пользователям
        self.allowed_paths = [
            '/admin/logout/',
            '/users/logout/',
            '/admin/',
        ]

    def __call__(self, request):
        # Проверяем только аутентифицированных пользователей
        if request.user.is_authenticated and not request.user.is_staff:
            # Проверяем, не забанен ли пользователь
            if request.user.is_banned():
                ban = request.user.get_active_ban()
                # Разрешаем доступ к некоторым путям
                if not any(request.path.startswith(path) for path in self.allowed_paths):
                    # Показываем сообщение о бане
                    if ban:
                        if ban.is_permanent:
                            messages.error(
                                request,
                                f'Ваш аккаунт заблокирован навсегда. Причина: {ban.reason}'
                            )
                        else:
                            messages.error(
                                request,
                                f'Ваш аккаунт заблокирован до {ban.ban_until.strftime("%d.%m.%Y %H:%M")}. '
                                f'Причина: {ban.reason}'
                            )
                    # Перенаправляем на страницу с информацией о бане
                    from django.http import HttpResponse
                    return HttpResponse(
                        f'''
                        <html>
                        <head><title>Аккаунт заблокирован</title></head>
                        <body style="font-family: Arial; text-align: center; padding: 50px;">
                            <h1 style="color: red;">Ваш аккаунт заблокирован</h1>
                            <p>{ban.reason if ban else "Неизвестная причина"}</p>
                            <p>{"Бан постоянный" if ban and ban.is_permanent else f"Бан до {ban.ban_until.strftime('%d.%m.%Y %H:%M')}" if ban else ""}</p>
                            <a href="/users/logout/">Выйти</a>
                        </body>
                        </html>
                        ''',
                        status=403
                    )

        response = self.get_response(request)
        return response

