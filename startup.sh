#!/bin/bash
gunicorn adminyoda.wsgi:application --bind 0.0.0.0:8000 &
python manage.py qcluster &

# Wait for any process to exit
wait -n

# Exit with status of process that exited first
exit $?
