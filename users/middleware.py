# users/middleware.py
from django.shortcuts import redirect
from django.http import HttpResponse
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
                    # Формируем информацию о бане
                    ban_reason = ban.reason if ban else "Неизвестная причина"
                    ban_info_html = ""
                    if ban:
                        if ban.is_permanent:
                            ban_info_html = '<div class="alert alert-warning" role="alert"><strong>Тип бана:</strong> Бан постоянный</div>'
                        elif ban.ban_until:
                            ban_date_str = ban.ban_until.strftime('%d.%m.%Y %H:%M')
                            ban_info_html = f'<div class="alert alert-warning" role="alert"><strong>Тип бана:</strong> Бан до {ban_date_str}</div>'
                    
                    # Возвращаем страницу с информацией о бане
                    html_content = f'''
                        <!DOCTYPE html>
                        <html lang="ru">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Аккаунт заблокирован</title>
                            <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.3.0/dist/css/bootstrap.min.css" rel="stylesheet">
                            <link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/bootstrap-icons@1.10.0/font/bootstrap-icons.css">
                        </head>
                        <body style="font-family: Arial, sans-serif; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); min-height: 100vh; display: flex; align-items: center; justify-content: center; padding: 20px;">
                            <div class="card shadow-lg" style="max-width: 600px; width: 100%;">
                                <div class="card-body text-center p-5">
                                    <div class="mb-4">
                                        <i class="bi bi-ban-fill text-danger" style="font-size: 4rem;"></i>
                                    </div>
                                    <h1 class="card-title text-danger mb-4">Ваш аккаунт заблокирован</h1>
                                    <div class="alert alert-danger" role="alert">
                                        <strong>Причина:</strong><br>
                                        {ban_reason}
                                    </div>
                                    {ban_info_html}
                                    <p class="text-muted mb-4">
                                        Если вы считаете, что это ошибка, свяжитесь с поддержкой.
                                    </p>
                                    <a href="/users/logout/" class="btn btn-primary btn-lg">
                                        <i class="bi bi-box-arrow-right me-2"></i>Выйти из аккаунта
                                    </a>
                                </div>
                            </div>
                        </body>
                        </html>
                    '''
                    return HttpResponse(html_content, status=403)

        response = self.get_response(request)
        return response

