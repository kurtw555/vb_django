from django.template.loader import render_to_string
from django.http import HttpResponse


def landing(request, page=""):
    html = render_to_string('index.html')
    response = HttpResponse()
    response.write(html)
    return response