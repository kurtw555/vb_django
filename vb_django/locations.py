from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from vb_django.validation import Validator
import numpy as np
import json
from vb_django.models import Location, Workflow, AnalyticalModel, AccessControlList


class LocationAPI:

    @staticmethod
    @require_http_methods(["POST"])
    def add_location(request):
        """
        Add a new location to the database, POST parameters for new location are:
        name, description, start_latitude, start_longitude, end_latitude, end_longitude, o_latitude, o_longitude
        The owner parameter is derived from the authentication process.
        :param request: The POST request.
        :return: If successful, the added model along with status=201, otherwise error message and status 400 or 401
        """
        required_parameters = [
            "name", "description",
            "start_latitude", "start_longitude",
            "end_latitude", "end_longitude",
            "o_latitude", "o_longitude"
        ]
        response = HttpResponse()
        if request.user.is_authenticated:
            location_details = request.POST.dict()
            missing_parameters = np.setdiff1d(location_details, required_parameters)
            if len(missing_parameters) > 0:
                # Validate each point, if invalid add to response content
                valid_points = True
                if not Validator.validate_point(location_details["start_latitude"], location_details["start_longitude"]):
                    response.content = "Invalid start point coordinates. Start latitude: {}, start longitude: {}\n" \
                        .format(location_details["start_latitude"], location_details["start_longitude"])
                    valid_points = False
                if not Validator.validate_point(location_details["end_latitude"], location_details["end_longitude"]):
                    response.content += "Invalid end point coordinates. End latitude: {}, End longitude: {}\n" \
                        .format(location_details["end_latitude"], location_details["end_longitude"])
                    valid_points = False
                if not Validator.validate_point(location_details["o_latitude"], location_details["o_longitude"]):
                    response.content += "Invalid orientation point coordinates. Orientation latitude: {}, Orientation longitude: {}" \
                        .format(location_details["end_latitude"], location_details["end_longitude"])
                    valid_points = False
                if valid_points:
                    new_location = Location(
                        owner=request.user,
                        name=location_details["name"],
                        description=location_details["description"],
                        start_latitude=location_details["start_latitude"],
                        start_longitude=location_details["start_longitude"],
                        end_latitude=location_details["end_latitude"],
                        end_longitude=location_details["end_longitude"],
                        o_latitude=location_details["o_latitude"],
                        o_longitude=location_details["o_longitude"]
                    )
                    new_location.save()
                    response.content = json.dumps(new_location)
                    response.status_code = 201
                else:
                    response.status_code = 400
            else:
                response.content = "Unable to add location, missing required parameter(s): {}" \
                    .format(",".join(missing_parameters))
                response.status_code = 400
        else:
            response.status_code = 401
        return response

    @staticmethod
    @require_http_methods(["GET"])
    def get_locations(request):
        """
        Gets all locations of the user, as well as all locations that the user has been given access to in the ACL
        :param request: The GET request
        :return: A dictionary of all user locations and shared locations and 200, or 401
        """
        response = HttpResponse()
        if request.user.is_authenticated:
            user = request.user
            user_locations = Location.objects.filter(owner=user)
            acl_locations = AccessControlList.objects.filter(target_user=user.id, object_type="Location") \
                .values_list('id', flat=True)
            shared_locations = Location.objects.filter(id__in=acl_locations)
            results = {"user_locations": user_locations, "shared_locations": shared_locations}
            response.content = results
            response.status_code = 200
        else:
            response.status_code = 401
        return response

    @staticmethod
    @require_http_methods(["PUT"])
    def edit_location(request):
        """
        Edit a specific location based upon ID.
        Possible conflict: if a completed model exists for the location, the model will no longer be compatible
        with new models if the location has changed [solution(s): 1) create new location if location has completed
        model, or 2) delete all workflows of completed models if the location has changed]. Solution 1 implemented.
        :param request: The PUT request
        :return: The updated object with status 200 on success, if new location created 201 , if fail 401
        """
        response = HttpResponse()
        if request.user.is_authenticated:
            location_details = request.PUT.dict()
            if "id" in location_details:
                current_location = Location.objects.filter(id=location_details["id"])
                location_models = AnalyticalModel.objects.filter(
                    workflow=Workflow.objects.filter(
                        location=current_location
                    )
                )
                existing_model = False
                for m in location_models:
                    if m.model is not None:
                        existing_model = True
                if existing_model:
                    new_location = Location(
                        owner=request.user,
                        name=location_details["name"],
                        description=location_details["description"],
                        start_latitude=location_details["start_latitude"],
                        start_longitude=location_details["start_longitude"],
                        end_latitude=location_details["end_latitude"],
                        end_longitude=location_details["end_longitude"],
                        o_latitude=location_details["o_latitude"],
                        o_longitude=location_details["o_longitude"]
                    )
                    new_location.save()
                    response.content = new_location
                    response.status_code = 201
                else:
                    current_location.name = location_details["name"]
                    current_location.description = location_details["description"]
                    current_location.start_latitude = location_details["start_latitude"]
                    current_location.start_longitude = location_details["start_longitude"]
                    current_location.end_latitude = location_details["end_latitude"]
                    current_location.end_longitude = location_details["end_longitude"]
                    current_location.o_latitude = location_details["o_latitude"]
                    current_location.o_longitude = location_details["o_longitude"]
                    current_location.save()
                    response.content = current_location
                    response.status_code = 200
        else:
            response.status_code = 401
        return response

    @staticmethod
    @require_http_methods(["DELETE"])
    def delete_location(request):
        """
        Deletes the specified location. Deletion is cascading, all objects that are dependent on the location will also be deleted.
        :param request: The DELETE request
        :return: 200 for a successful deletion, 400 for an invalid request, or a 401 for authorized request
        """
        response = HttpResponse()
        if request.user.is_authenticated:
            location_details = request.DELETE.dict()
            if "id" in location_details:
                Location.objects.filter(id=location_details["id"]).delete()
                response.status_code = 200
            else:
                response.status_code = 400
                response.content = "Deletion request requires 'id' parameter"
        else:
            response.status_code = 401
        return response
