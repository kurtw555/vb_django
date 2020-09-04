FROM python:3.8.2-slim

ARG APP_USER=appuser
RUN groupadd -r ${APP_USER} && useradd --no-log-init -r -g ${APP_USER} ${APP_USER}

RUN apt-get update
RUN apt-get install -y python-pip libpq-dev python-dev
RUN python -m pip install --upgrade pip setuptools wheel

RUN mkdir -p /opt/app

COPY requirements.txt /opt/app/requirements.txt
RUN pip install -r /opt/app/requirements.txt
RUN pip install uwsgi==2.0.19.1

COPY vb_django/uwsgi.ini /etc/uwsgi/
COPY start-server.sh /opt/app/start-server.sh
RUN chown -R www-data:www-data /opt/app
RUN chmod 755 /opt/app/start-server.sh

WORKDIR /opt/app
ENV PYTHONPATH="/opt/app:/opt/app/vb_django:${PYTHONPATH}"
USER ${APP_USER}:${APP_USER}
CMD ["sh", "/opt/app/start-server.sh"]