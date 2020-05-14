FROM python:3.8.2-slim

ARG APP_USER=appuser
RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER}

RUN apt-get update
RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/pip_cache

COPY vb_django/uwsgi.ini /etc/uwsgi/
COPY . /opt/app
WORKDIR /opt/app
RUN pip install --no-cache-dir -r requirements.txt /opt/app/pip_cache
RUN chown -R www-data:www-data /opt/app
RUN chmod 755 /opt/app/start-server.sh

EXPOSE 8080
ENV DJANGO_SETTINGS_MODULE=settings
USER ${APP_USER}:${APP_USER}
CMD ["/opt/app/start-server.sh"]