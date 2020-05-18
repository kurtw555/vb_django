from django.http import HttpResponse
from django.views.decorators.http import require_http_methods
from vb_django.validation import Validator
from vb_django.models import Location, Workflow, AccessControlList
from vb_django.acl import Authorization


class WorkflowAPI:

    @staticmethod
    @require_http_methods(["GET"])
    def get_workflows(request):
        """
        GET request to get all workflows that the current logged in user has access to.
        :param request: The GET request
        :return: A list of all workflows where the user is the owner of the corresponding location, or has access to.
        """
        response = HttpResponse()
        if request.user.is_authenticated:
            user = request.user
            workflows = Workflow.objects.filter(location__owner=user)
            acl_workflows = AccessControlList.objects.filter(target_user=user, object_type="Workflow")\
                .values_list('id', flat=True)
            shared_workflows = Workflow.objects.filter(id__in=acl_workflows)
            results = {"user_workflows": workflows, "shared_workflows": shared_workflows}
            response.status_code = 200
            response.content = results
        else:
            response.status_code = 401
        return response

    @staticmethod
    @require_http_methods(["POST"])
    def add_workflow(request):
        """
        POST request to create a new workflow for the specified location
        :param request: The POST request, requires a 'name', 'description' and 'location' parameter, where location is
        the id of the location for the new workflow.
        :return: The successfully added workflow 201, unauthenticated 401, invalid/missing parameters 400
        """
        required_parameters = ["location", "description", "name"]
        response = HttpResponse()
        if request.user.is_authenticated:
            workflow_inputs = request.POST.dict()
            missing_parameters = Validator.validate_inputlist(required_parameters, workflow_inputs.keys())
            if len(missing_parameters) != 0:
                location = Location.objects.filter(id=workflow_inputs["location"])
                workflow = Workflow(
                    location=location,
                    name=workflow_inputs["name"],
                    description=workflow_inputs["description"]
                )
                workflow.save()
                response.content = workflow
                response.status_code = 201
            else:
                response.content = missing_parameters
                response.status_code = 400
        else:
            response.status_code = 401
        return response

    @staticmethod
    @require_http_methods(["PUT"])
    def edit_workflow(request):
        """
        PUT request to edit an existing workflow (changing of the name or description does not alter the integrity of
        the analytical model data or dataset).
        :param request: The PUT request, requires a 'name', 'description' and 'location' parameter, where location is
        the id of the location for the new workflow.
        :return: The successfully edited workflow 201, unauthenticated 401, unauthorized 403, and
        invalid/missing parameters 400
        """
        required_parameters = ["id", "location", "description", "name"]
        response = HttpResponse()
        if request.user.is_authenticated:
            workflow_inputs = request.PUT.dict()
            missing_parameters = Validator.validate_inputlist(required_parameters, workflow_inputs.keys())
            if len(missing_parameters) != 0:
                location = Location.objects.filter(id=workflow_inputs["location"])
                authorized = Authorization().check_authorization(
                    user=request.user,
                    object_type="Location",
                    object_id=workflow_inputs["location"]
                )
                # TODO: Allow authorized users to edit workflow?
                if location.owner == request.user:
                    workflow = Workflow.objects.filter(id=workflow_inputs["id"])
                    if workflow is not None:
                        workflow.name = workflow_inputs["name"]
                        workflow.description = workflow_inputs["description"]
                        workflow.save()
                        response.content = workflow
                        response.status_code = 201
                    else:
                        response.status_code = 400
                        response.content = "Requested workflow id not found. ID: {}".format(workflow_inputs["id"])
                else:
                    response.status_code = 403
            else:
                response.content = missing_parameters
                response.status_code = 400
        else:
            response.status_code = 401
        return response

    @staticmethod
    @require_http_methods(["DELETE"])
    def delete_workflow(request):
        """
        DELETE request to delete an existing workflow.
        :param request: Requires an 'id' parameter
        :return: The successfully deleting workflow 200, unauthenticated 401, unauthorized 403, and
        invalid/missing parameters 400
        """
        required_parameters = ["id"]
        response = HttpResponse()
        if request.user.is_authenticated:
            params = request.PUT.dict()
            missing_parameters = Validator.validate_inputlist(required_parameters, params.keys())
            if len(missing_parameters) != 0:
                workflow = Workflow.objects.filter(id=params["id"])
                if workflow is not None:
                    if workflow.location.owner == request.user:
                        workflow.delete()
                    else:
                        response.status_code = 403
                else:
                    response.status_code = 400
                    response.content = "Requested workflow not found. ID: {}".format(params["id"])
            else:
                response.content = missing_parameters
                response.status_code = 400
        else:
            response.status_code = 401
        return response
