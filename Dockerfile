FROM python:3.11

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    apt-get install -y netcat-traditional && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

COPY . .

RUN chmod +x entrypoint.sh

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

EXPOSE 8000
CMD sh -c "python manage.py runserver 0.0.0.0:8000"