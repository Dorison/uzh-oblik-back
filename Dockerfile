# Використовуйте офіційний образ Python
FROM python:3.8-slim

# Встановіть залежності додатку
RUN pip install flask

# Створіть робочий каталог
WORKDIR /app

# Скопіюйте файли додатку в робочий каталог
COPY . /app

# Встановіть потрібні пакети (якщо є)
# RUN pip install -r requirements.txt

# Запустіть додаток
CMD ["python", "app.py"]
