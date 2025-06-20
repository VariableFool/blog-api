# Используем официальный Python-образ
FROM python:3.11-slim

# Устанавливаем рабочую директорию
WORKDIR /app

# Копируем зависимости
COPY requirements.txt ./

# Устанавливаем зависимости
RUN pip install --no-cache-dir -r requirements.txt

# Копируем всё приложение
COPY . .

# Создаем папки для загрузок (на всякий случай)
RUN mkdir -p uploads/userbanner

# Указываем порт
EXPOSE 3001

# Устанавливаем переменную окружения (название WSGI-приложения)
ENV FLASK_APP=app.py

# Запускаем через gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:3001", "app:application"]
