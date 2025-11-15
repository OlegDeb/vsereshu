# Инструкция по применению миграций для системы банов и жалоб

## Проблема
На сервере есть изменения в моделях, которые не отражены в миграциях.

## Решение

### Вариант 1: Создать миграции на сервере (рекомендуется)

1. **Создать миграции для users:**
```bash
python3 manage.py makemigrations users
```

2. **Создать миграции для services (если нужно):**
```bash
python3 manage.py makemigrations services
```

3. **Применить миграции:**
```bash
python3 manage.py migrate users
python3 manage.py migrate services
# Или применить все:
python3 manage.py migrate
```

### Вариант 2: Скопировать миграцию с локальной машины

Если на локальной машине уже есть миграция `0003_userban_usercomplaint_userwarning.py`, 
скопируйте её на сервер:

```bash
# С локальной машины
scp users/migrations/0003_userban_usercomplaint_userwarning.py user@server:/path/to/project/users/migrations/

# Затем на сервере
python3 manage.py migrate users
```

## Проверка

После применения миграций проверьте:

1. **Статус миграций:**
```bash
python3 manage.py showmigrations users
```

Должна быть отмечена: `[X] 0003_userban_usercomplaint_userwarning`

2. **Проверка в админ-панели:**
   - Зайдите в Django Admin
   - Должны появиться разделы:
     - Предупреждения (UserWarning)
     - Баны (UserBan)
     - Жалобы (UserComplaint)

3. **Проверка таблиц в БД:**
```sql
-- PostgreSQL
\dt users_user*
-- Должны быть:
-- users_userban
-- users_usercomplaint
-- users_userwarning
```

## Если возникли ошибки

Если при применении миграций возникли ошибки:

1. **Проверьте, что middleware добавлен в settings.py:**
```python
MIDDLEWARE = [
    ...
    'users.middleware.BanCheckMiddleware',  # Проверка банов
    ...
]
```

2. **Проверьте, что все файлы скопированы:**
   - `users/models.py` (с новыми моделями)
   - `users/admin.py` (с новыми админ-классами)
   - `users/middleware.py` (новый файл)
   - `users/forms.py` (с новыми формами)
   - `users/views.py` (с новыми представлениями)
   - `users/urls.py` (с новыми URL)
   - Все шаблоны в `templates/users/`

3. **Если нужно откатить миграцию:**
```bash
python3 manage.py migrate users 0002_alter_customuser_avatar
```

4. **Затем применить заново:**
```bash
python3 manage.py migrate users
```

