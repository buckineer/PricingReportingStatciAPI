FROM python:3.7.6-buster
MAINTAINER bertrand@viridios.ai
WORKDIR /app
ADD requirements.txt .
RUN pip install -r requirements.txt
COPY . .
ENV APP_SETTINGS $APP_SETTINGS
ENV MYSQL_DATABASE $MYSQL_DATABASE
ENV MYSQL_HOST $MYSQL_HOST
ENV MYSQL_ROOT_PASSWORD $MYSQL_ROOT_PASSWORD
CMD [ "python", "/app/main.py" ]