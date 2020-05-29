from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from vb_django.models import Workflow
from vb_django.serializers import WorkflowSerializer
from vb_django.permissions import IsOwnerOfLocationChild


class WorkflowView(viewsets.ViewSet):
    """
    The Workflow API endpoint viewset for managing user workflows in the database.
    """
    serializer_class = WorkflowSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOfLocationChild]

    def list(self, request, pk=None):
        """
        GET request that lists all the workflows for a specific location id
        :param request: GET request, containing the location id as 'location'
        :return: List of workflows
        """
        if 'location_id' in self.request.query_params.keys():
            workflows = Workflow.objects.filter(location_id=int(self.request.query_params.get('location_id')))
            # TODO: Add ACL access objects
            serializer = self.serializer_class(workflows, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            "Required 'location' parameter for the location id was not found.",
            status=status.HTTP_400_BAD_REQUEST
        )

    def create(self, request):
        """
        POST request that creates a new workflow.
        :param request: POST request
        :return: New workflow object
        """
        workflow_inputs = request.data.dict()
        serializer = self.serializer_class(data=workflow_inputs, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            workflow = serializer.data
            if workflow:
                return Response(workflow, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        """
        PUT request for updating a workflow, if update will cause lose of analytical model integrity, a new workflow is
        created.
        :param request: PUT request
        :return: The updated/200 or new/201 workflow
        """
        serializer = self.serializer_class(data=request.data.dict(), context={'request': request})
        if serializer.is_valid() and pk is not None:
            try:
                original_workflow = Workflow.objects.get(id=int(pk))
            except Workflow.DoesNotExist:
                return Response(
                    "No workflow found for id: {}".format(pk),
                    status=status.HTTP_400_BAD_REQUEST
                )
            if IsOwnerOfLocationChild().has_object_permission(request, self, original_workflow):
                workflow = serializer.update(original_workflow, serializer.validated_data)
                if workflow:
                    response_status = status.HTTP_201_CREATED
                    response_data = serializer.data
                    response_data["id"] = workflow.id
                    if int(pk) == workflow.id:
                        response_status = status.HTTP_200_OK
                    return Response(response_data, status=response_status)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        """
        DELETE request for removing the workflow from the location, cascading deletion for elements in database.
        Front end should require verification of action.
        :param request: DELETE request
        :return:
        """
        if pk is not None:
            try:
                workflow = Workflow.objects.get(id=int(pk))
            except Workflow.DoesNotExist:
                return Response("No workflow found for id: {}".format(pk), status=status.HTTP_400_BAD_REQUEST)
            if IsOwnerOfLocationChild().has_object_permission(request, self, workflow):
                workflow.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response("No workflow 'id' in request.", status=status.HTTP_400_BAD_REQUEST)
