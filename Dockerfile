FROM python:3.8

WORKDIR /usr/src/app

COPY requirements.txt ./

RUN apt-get update && \
    apt-get install -y --no-install-recommends postgresql-client && \
    rm -rf /var/lib/apt/lists/* && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

COPY ./entrypoint.sh .
RUN chmod +x ./entrypoint.sh

COPY . .

RUN chown -R 1001:1001 /usr/src/app/output

ENTRYPOINT ["/usr/src/app/entrypoint.sh"]

EXPOSE 8000
CMD sh -c "python manage.py runserver 0.0.0.0:8000"