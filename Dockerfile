FROM python:3.8.2

RUN apt-get update
RUN mkdir -p /opt/app
RUN mkdir -p /opt/app/pip_cache

COPY vb_django/uwsgi.ini /etc/uwsgi/
COPY . /opt/app
WORKDIR /opt/app
RUN pip install -r requirements.txt --cache-dir /opt/app/pip_cache
RUN chown -R www-data:www-data /opt/app
RUN chmod 755 /opt/app/start-server.sh

EXPOSE 8080
CMD ["/opt/app/start-server.sh"]