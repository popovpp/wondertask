FROM python:3.8.5

ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
COPY . /code/
WORKDIR /code

RUN pip3 install -r requirements.txt

ARG DJANGO_SETTINGS_MODULE=""
ARG SECRET_KEY=""
ARG DEBUG="true"
# Postgres
ARG API_PG_DB=""
ARG API_PG_USER=""
ARG API_PG_PASSWORD=""
ARG API_PG_HOST=localhost
ARG API_PG_PORT=5432

ARG FCM_API_KEY=""

ENV DJANGO_SETTINGS_MODULE=$DJANGO_SETTINGS_MODULE
ENV SECRET_KEY=$SECRET_KEY
ENV DEBUG=$DEBUG
ENV API_PG_DB=$API_PG_DB
ENV API_PG_USER=$API_PG_USER
ENV API_PG_PASSWORD=$API_PG_PASSWORD
ENV API_PG_HOST=$API_PG_HOST
ENV API_PG_PORT=$API_PG_PORT

ENV FCM_API_KEY=$FCM_API_KEY

ENV PYTHONPATH "${PYTHONPATH}:/code"

# RUN python3.8 ./manage.py makemigrations
# CMD ["python3.8",  "./manage.py", "runserver 0.0.0.0:9007"]
