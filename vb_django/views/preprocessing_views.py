from rest_framework import viewsets, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from vb_django.models import PreProcessingConfig
from vb_django.serializers import PreProcessingConfigSerializer
from vb_django.permissions import IsOwnerOfWorkflowChild
from vb_django.app.preprocessing import DAGFunctions
import json


class PreProcessingConfigView(viewsets.ViewSet):
    """
    The Dataset API endpoint viewset for managing user datasets in the database.
    """
    serializer_class = PreProcessingConfigSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOfWorkflowChild]

    def list(self, request, pk=None):
        """
        GET request that lists all the Pre-Processing Config for a specific workflow id
        :param request: GET request, containing the workflow id as 'workflow'
        :return: List of pre-processing configurations
        """
        if 'workflow_id' in self.request.query_params.keys():
            pp_configs = PreProcessingConfig.objects.filter(workflow_id=int(self.request.query_params.get('workflow_id')))
            serializer = self.serializer_class(pp_configs, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            "Required 'workflow_id' parameter for the workflow id was not found.",
            status=status.HTTP_400_BAD_REQUEST
        )

    def create(self, request):
        """
        POST request that creates a new pre-processing configuration.
        :param request: POST request
        :return: New dataset
        """
        inputs = request.data.dict()
        serializer = self.serializer_class(data=inputs, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            pp_config = serializer.data
            if pp_config:
                return Response(pp_config, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        serializer = self.serializer_class(data=request.data.dict(), context={'request': request})
        if serializer.is_valid() and pk is not None:
            try:
                original_pp_config = PreProcessingConfig.objects.get(id=int(pk))
            except PreProcessingConfig.DoesNotExist:
                return Response(
                    "No pre-processing config found for id: {}".format(pk),
                    status=status.HTTP_400_BAD_REQUEST
                )
            if IsOwnerOfWorkflowChild().has_object_permission(request, self, original_pp_config):
                amodel = serializer.update(original_pp_config, serializer.validated_data)
                if amodel:
                    response_status = status.HTTP_201_CREATED
                    response_data = serializer.data
                    response_data["id"] = amodel.id
                    if int(pk) == amodel.id:
                        response_status = status.HTTP_200_OK
                    return Response(response_data, status=response_status)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        if pk is not None:
            try:
                pp_config = PreProcessingConfig.objects.get(id=int(pk))
            except PreProcessingConfig.DoesNotExist:
                return Response("No pre-processing config found for id: {}".format(pk), status=status.HTTP_400_BAD_REQUEST)
            if IsOwnerOfWorkflowChild().has_object_permission(request, self, pp_config):
                pp_config.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response("No pre-processing config 'id' in request.", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["get"], name="Preprocessing operations list")
    def get_operations(self, request):
        operations = list(dir(DAGFunctions))[26:]
        return Response({"operations": operations}, status=status.HTTP_200_OK)

