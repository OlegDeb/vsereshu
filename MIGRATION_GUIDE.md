# Руководство по миграциям на сервере

## Важно перед началом!

**⚠️ Обязательно сделайте резервную копию базы данных перед применением миграций!**

```bash
# Для PostgreSQL
pg_dump -U username database_name > backup_$(date +%Y%m%d_%H%M%S).sql

# Для SQLite
cp db.sqlite3 db.sqlite3.backup_$(date +%Y%m%d_%H%M%S)
```

## Последовательность действий на сервере

### Вариант 1: Автоматический (рекомендуется)

Используйте готовый скрипт:

```bash
# Перейдите в директорию проекта
cd /path/to/vsereshu

# Если используете виртуальное окружение
source venv/bin/activate  # или ваш путь к venv

# Если используете settings_prod.py
export DJANGO_SETTINGS_MODULE=config.settings_prod

# Сделайте скрипт исполняемым (если еще не сделано)
chmod +x migrate_all.sh

# Запустите скрипт
./migrate_all.sh
```

### Вариант 2: Ручной (пошаговый)

#### Шаг 1: Создание миграций (если нужно)

Если на сервере еще нет файлов миграций, создайте их:

```bash
# Перейдите в директорию проекта
cd /path/to/vsereshu

# Активируйте виртуальное окружение (если используется)
source venv/bin/activate

# Установите переменную окружения для продакшена (если нужно)
export DJANGO_SETTINGS_MODULE=config.settings_prod

# Создайте миграции для всех приложений
python manage.py makemigrations users
python manage.py makemigrations categories
python manage.py makemigrations regions'
python manage.py makemigrations tasks
python manage.py makemigrations services
python manage.py makemigrations articles
python manage.py makemigrations pages

# Или создайте все сразу
python manage.py makemigrations
```

#### Шаг 2: Применение миграций в правильном порядке

**Порядок важен из-за зависимостей между моделями!**

```bash
# 1. Сначала users (базовая модель пользователя)
python manage.py migrate users

# 2. Затем categories (категории используются другими моделями)
python manage.py migrate categories

# 3. Затем regions (регионы и города)
python manage.py migrate regions

# 4. Затем tasks (зависит от categories и regions)
python manage.py migrate tasks

# 5. Затем services (зависит от users, categories и regions)
python manage.py migrate services

# 6. Остальные приложения
python manage.py migrate articles
python manage.py migrate pages

# 7. Применение всех остальных миграций (admin, auth, sessions и т.д.)
python manage.py migrate
```

### Вариант 3: Применить все миграции сразу (если зависимости настроены правильно)

```bash
python manage.py migrate
```

Django автоматически определит правильный порядок на основе зависимостей.

## Проверка статуса миграций

После применения миграций проверьте статус:

```bash
python manage.py showmigrations
```

Все миграции должны быть помечены как `[X]` (применены).

## Если возникли ошибки

### Ошибка: "No such table" или "column does not exist"

Это означает, что миграции применены не в правильном порядке или не полностью.

**Решение:**
1. Проверьте, какие миграции применены: `python manage.py showmigrations`
2. Примените недостающие миграции вручную в правильном порядке
3. Если проблема сохраняется, возможно потребуется откат и повторное применение

### Ошибка: "Migration dependencies reference nonexistent migration"

Это означает, что файлы миграций не синхронизированы.

**Решение:**
1. Убедитесь, что все файлы миграций скопированы на сервер
2. Проверьте, что в `INSTALLED_APPS` в `settings.py` указаны все приложения
3. Пересоздайте миграции: `python manage.py makemigrations`

### Ошибка: "Table already exists"

Это означает, что таблица уже создана, но миграция не отмечена как примененная.

**Решение:**
1. Отметьте миграцию как примененную (fake): 
   ```bash
   python manage.py migrate --fake app_name migration_name
   ```
2. Или удалите таблицу вручную и примените миграцию заново (⚠️ только если нет важных данных!)

## Основные изменения в этой версии

1. **tasks**: Добавлено поле `views` (миграция `0008_task_views_alter_task_location_type.py`)
2. **services**: Новое приложение с моделями `Service` и `ServiceMessage`
   - Миграция `0001_initial.py` - создание моделей Service
   - Миграция `0002_alter_service_location_type_servicemessage.py` - обновление LocationType и добавление ServiceMessage

## После применения миграций

1. Соберите статические файлы (если нужно):
   ```bash
   python manage.py collectstatic --noinput
   ```

2. Перезапустите веб-сервер (nginx, gunicorn, uwsgi и т.д.)

3. Проверьте работу сайта

## Полезные команды

```bash
# Показать все миграции и их статус
python manage.py showmigrations

# Показать SQL, который будет выполнен для миграции
python manage.py sqlmigrate app_name migration_number

# Откатить последнюю миграцию
python manage.py migrate app_name previous_migration_number

# Применить конкретную миграцию
python manage.py migrate app_name migration_number
```

