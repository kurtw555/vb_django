# from django.http import HttpResponse
# from django.views.decorators.http import require_http_methods
# from vb_django.models import Location, LocationMetadata
# from vb_django.acl import Authorization
#
#
# class LocationMetadataAPI:
#
#     @staticmethod
#     @require_http_methods(["GET"])
#     def get_metadata(request):
#         """
#         Gets all location metadata for the location
#         :param request: The GET request
#         :return: A dictionary of all user locations and shared locations and 200, or 401
#         """
#         response = HttpResponse()
#         if request.user.is_authenticated:
#             params = request.GET.dict()
#             if "id" in params:
#                 location = Location.objects.filter(owner=request.user, id=params["id"])
#                 authorized = Authorization().check_authorization(
#                     user=request.user, object_type="Location", object_id=params["id"])
#                 if authorized:
#                     metadata = LocationMetadata.objects.filter(location=location)
#                     response.content = metadata
#                     response.status_code = 200
#                 else:
#                     response.status_code = 403
#         else:
#             response.status_code = 401
#         return response
#
#     @staticmethod
#     @require_http_methods(["POST"])
#     def add_metadata(request):
#         response = HttpResponse()
#         if request.user.is_authenticated:
#             metadata = request.POST.dict()
#             if "id" not in metadata:
#                 response.status_code = 400
#                 response.content = "No id found in request parameters."
#             else:
#                 location = Location.objects.filter(id=metadata["id"])
#                 authorized = Authorization().check_authorization(
#                     user=request.user, object_type="Location", object_id=metadata["id"])
#                 if "name" in metadata and "value" in metadata:
#                     if location is None:
#                         response.status_code = 400
#                         response.content = "No location "
#                     else:
#                         # TODO: Behavior for same name entries
#                         if authorized:
#                             meta = LocationMetadata(location=location, name=metadata["name"], value=metadata["value"])
#                             meta.save()
#                         else:
#                             response.status_code = 403
#                 else:
#                     response.status_code = 400
#                     response.content = "No name and value found in request parameters."
#         else:
#             response.status_code = 401
#         return response
#
#     @staticmethod
#     @require_http_methods(["DELETE"])
#     def delete_metadata(request):
#         response = HttpResponse()
#         if request.user.is_authenticated:
#             metadata = request.DELETE.dict()
#             if "id" not in metadata:
#                 response.status_code = 400
#                 response.content = "No id found in request parameters."
#             else:
#                 location = Location.objects.filter(id=metadata["id"])
#                 owner = Authorization().get_owner(
#                     object_type="Location", object_id=metadata["id"])
#                 if "name" in metadata and "value" in metadata:
#                     if location is None:
#                         response.status_code = 400
#                         response.content = "No location "
#                     else:
#                         if owner == request.user:
#                             LocationMetadata.objects.filter(location=location, name=metadata["name"]).delete()
#                             response.status_code = 200
#                         else:
#                             response.status_code = 403
#                 else:
#                     response.status_code = 400
#                     response.content = "No name and/or value found in request parameters."
#         else:
#             response.status_code = 401
#         return response
#
#     @staticmethod
#     @require_http_methods(["PUT"])
#     def edit_metadata(request):
#         response = HttpResponse()
#         if request.user.is_authenticated:
#             metadata = request.PUT.dict()
#             if "id" not in metadata:
#                 response.status_code = 400
#                 response.content = "No id found in request parameters."
#             else:
#                 location = Location.objects.filter(id=metadata["id"])
#                 owner = Authorization().get_owner(
#                     object_type="Location", object_id=metadata["id"])
#                 if "name" in metadata and "value" in metadata:
#                     if location is None:
#                         response.status_code = 400
#                         response.content = "No location "
#                     else:
#                         if owner == request.user:
#                             meta = LocationMetadata.objects.filter(location=location, name=metadata["name"])
#                             meta.value = metadata["value"]
#                             meta.save()
#                             response.content = meta
#                             response.status_code = 200
#                         else:
#                             response.status_code = 403
#                 else:
#                     response.status_code = 400
#                     response.content = "No name and/or value found in request parameters."
#         else:
#             response.status_code = 401
#         return response
