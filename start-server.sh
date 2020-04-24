#!/bin/bash

django-admin.py collectstatic --noinput
django-admin migrate auth --noinput
django-admin migrate sessions --noinput

exec uwsgi /etc/uwsgi/uwsgi.ini