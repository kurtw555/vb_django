from django.http import JsonResponse, HttpResponseBadRequest
from django.contrib.auth.models import User
from django.views.decorators.http import require_GET, require_POST
from django.contrib.auth import authenticate, login
import json


class VBUser:

    @staticmethod
    @require_POST
    def register(request):
        if len(request.POST) == 0:
            try:
                r = json.loads(request.body)
            except json.JSONDecodeError:
                return HttpResponseBadRequest
        else:
            r = request.POST.dict()
        if "username" not in r or "email" not in r or "password" not in r:
            return HttpResponseBadRequest
        user = User.objects.create_user(r["username"], r["email"], r["password"])
        if user is None:
            return HttpResponseBadRequest
        user.save()
        auth_user = authenticate(request, username=r["username"], password=r["password"])
        if auth_user is not None:
            login(request, auth_user)
            response = JsonResponse({"username": user.username, "email": user.email})
            response.status_code = 201
            return response
        return HttpResponseBadRequest

    @staticmethod
    @require_POST
    def login(request):
        if len(request.POST) == 0:
            try:
                r = json.loads(request.body)
            except json.JSONDecodeError:
                return HttpResponseBadRequest
        else:
            r = request.POST.dict()
        if "username" not in r or "password" not in r:
            return HttpResponseBadRequest
        auth_user = authenticate(request, username=r["username"], password=r["password"])
        if auth_user is not None:
            login(request, auth_user)
            response = JsonResponse({"username": auth_user.username, "email": auth_user.email})
            response.status_code = 200
            return response
        return HttpResponseBadRequest

    @staticmethod
    @require_GET
    def reset_password(request):
        # TODO: Implement password reset
        return HttpResponseBadRequest
