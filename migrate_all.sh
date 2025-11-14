#!/bin/bash
# Скрипт для применения миграций в правильном порядке

# Переход в директорию проекта (где находится manage.py)
cd "$(dirname "$0")"

# Проверка наличия manage.py
if [ ! -f "manage.py" ]; then
    echo "Ошибка: manage.py не найден. Убедитесь, что вы запускаете скрипт из корня проекта."
    exit 1
fi

# Определение команды python (python3 или python)
if command -v python3 &> /dev/null; then
    PYTHON_CMD="python3"
else
    PYTHON_CMD="python"
fi

# Если используется виртуальное окружение, можно раскомментировать следующую строку:
# source venv/bin/activate  # или путь к вашему виртуальному окружению

# Если используется settings_prod.py, можно установить переменную окружения:
# export DJANGO_SETTINGS_MODULE=config.settings_prod

echo "Применение миграций в правильном порядке..."
echo "Используется: $PYTHON_CMD"

# 1. Сначала users (базовая модель пользователя)
echo "1. Применение миграций users..."
$PYTHON_CMD manage.py migrate users

# 2. Затем categories (включая все миграции)
echo "2. Применение миграций categories..."
$PYTHON_CMD manage.py migrate categories

# 3. Затем regions
echo "3. Применение миграций regions..."
$PYTHON_CMD manage.py migrate regions

# 4. Затем tasks (зависит от categories и regions)
echo "4. Применение миграций tasks..."
$PYTHON_CMD manage.py migrate tasks

# 5. Затем services (зависит от users, categories и regions)
echo "5. Применение миграций services..."
$PYTHON_CMD manage.py migrate services

# 6. Остальные приложения
echo "6. Применение миграций articles..."
$PYTHON_CMD manage.py migrate articles

echo "7. Применение миграций pages..."
$PYTHON_CMD manage.py migrate pages

# 8. Применение всех остальных миграций (admin, auth, sessions и т.д.)
echo "8. Применение остальных миграций..."
$PYTHON_CMD manage.py migrate

echo "Все миграции применены!"

