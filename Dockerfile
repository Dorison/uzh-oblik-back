FROM python:3.8-slim
COPY requirements.txt .
RUN apt-get update \
    && apt-get -y install libpq-dev gcc
RUN pip install --no-cache-dir -r requirements.txt
WORKDIR /app
COPY . /app
CMD ["python", "app.py"]
