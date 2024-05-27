FROM python:3.7.6-buster
MAINTAINER bertrand@viridios.ai
WORKDIR /app
ADD requirements.txt .
ADD alembic.ini .
ADD main.py .
ADD config.py .
ADD database.py .
ADD models.py .
ADD security.py .
ADD attributes.py .
ADD helpers.py .
ADD route_classes.py .
RUN pip install -r requirements.txt
COPY alembic/ alembic/
COPY api/ api/
COPY crud/ crud/
COPY core/ core/
COPY schemas/ schemas/
COPY tests/ tests/
ENV APP_SETTINGS $APP_SETTINGS
ENV MYSQL_DATABASE $MYSQL_DATABASE
ENV MYSQL_HOST $MYSQL_HOST
ENV MYSQL_ROOT_PASSWORD $MYSQL_ROOT_PASSWORD
CMD ["python","/app/main.py"]
