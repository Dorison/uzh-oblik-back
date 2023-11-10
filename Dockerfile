FROM python:3.8-slim
RUN pip install flask
WORKDIR /app
COPY . /app
CMD ["python", "app.py"]
