FROM python:3.12

ENV APP_HOME /app

WORKDIR $APP_HOME

COPY requirements.txt /app

RUN pip install -r requirements.txt

COPY . /app

EXPOSE 3000

CMD ["python", "webserver/main.py"]