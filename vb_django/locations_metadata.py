from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from vb_django.models import Location, LocationMetadata, Workflow, AnalyticalModel, AccessControlList


class LocationMetadataAPI:

    @staticmethod
    @require_http_methods(["POST"])
    def add_metadata(request):
        response = HttpResponse()
        if request.user.is_authenticated:
            metadata = request.POST.dict()
            if "id" not in metadata:
                response.status_code = 400
                response.content = "No id found in request parameters."
            else:
                if "name" in metadata and "value" in metadata:
                    location = Location.objects.filter(id=metadata["id"])
                    if location is None:
                        response.status_code = 400
                        response.content = "No location "
                    else:
                        # TODO: Behavior for same name entries
                        meta = LocationMetadata(location=location, name=metadata["name"], value=metadata["value"])
                        meta.save()
                else:
                    response.status_code = 400
                    response.content = "No name and value found in request parameters."
        else:
            response.status_code = 401
        return response
