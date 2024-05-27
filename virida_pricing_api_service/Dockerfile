FROM blenezet/virida_tensorflow
MAINTAINER bertrand@viridios.ai
WORKDIR /app
ADD sa_credentials.json .
ADD requirements.txt .
ADD alembic.ini .
ADD main.py .
ADD config.py .
ADD database.py .
ADD models.py .
ADD security.py .
ADD httpclient.py .
ADD email_client.py .
ADD pricing_router.py .
ADD snap_forex.py .
ADD snap_eua.py .
ADD snap_atmospheric_co2.py .
ADD snap_brent_europe.py .
ADD snap_treasury_curve_slope.py .
ADD snap_interest_rate_curve.py .
ADD end_of_day.py .
COPY alembic/ alembic/
COPY api/ api/
COPY core/ core/
COPY crud/ crud/
COPY schemas/ schemas/
COPY helpers/ helpers/
COPY tests/ tests/
RUN pip3 install -r requirements.txt
ENV APP_SETTINGS $APP_SETTINGS
ENV MYSQL_DATABASE $MYSQL_DATABASE
ENV MYSQL_HOST $MYSQL_HOST
ENV MYSQL_ROOT_PASSWORD $MYSQL_ROOT_PASSWORD
ENV GOOGLE_APPLICATION_CREDENTIALS $GOOGLE_APPLICATION_CREDENTIALS
CMD ["python","/app/main.py"]
