#!/bin/bash

if [ ! -d "/opt/app/vb_django/static" ]
then
  mkdir /opt/app/vb_django/static
fi
django-admin collectstatic --noinput
django-admin migrate --noinput
django-admin migrate auth --noinput
django-admin migrate sessions --noinput
django-admin runserver --verbosity 3 0.0.0.0:8080
# exec uwsgi /etc/uwsgi/uwsgi.ini --show-config