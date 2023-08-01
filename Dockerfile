FROM python:3.8

WORKDIR /usr/src/app
COPY . .
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        postgresql-client \
    && rm -rf /var/lib/apt/lists/* \
    && pip install -r requirements.txt

EXPOSE 8000
CMD sh -c "python manage.py runserver 0.0.0.0:8000"