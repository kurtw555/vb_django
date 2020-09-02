from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from vb_django.models import AnalyticalModel
from vb_django.app.metadata import Metadata
from vb_django.serializers import AnalyticalModelSerializer
from vb_django.permissions import IsOwnerOfWorkflowChild


class AnalyticalModelView(viewsets.ViewSet):
    """
    The Analytical Model API endpoint viewset for managing user analytical models in the database.
    """
    serializer_class = AnalyticalModelSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOfWorkflowChild]

    def list(self, request):
        """
        GET request that lists all the analytical models for a specific workflow id
        :param request: GET request, containing the workflow id as 'workflow'
        :return: List of analytical models
        """
        if 'workflow_id' in self.request.query_params.keys():
            a_models = AnalyticalModel.objects.filter(workflow_id=int(self.request.query_params.get('workflow_id')))
            serializer = self.serializer_class(a_models, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            "Required 'workflow' parameter for the workflow id was not found.",
            status=status.HTTP_400_BAD_REQUEST
        )

    def create(self, request):
        """
        POST request that creates a new analytical model.
        :param request: POST request
        :return: New analytical object
        """
        amodel_inputs = request.data.dict()
        serializer = self.serializer_class(data=amodel_inputs, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            amodel_inputs = serializer.data
            if "metadata" in amodel_inputs.keys():
                amodel_inputs["metadata"] = None
                m = Metadata(amodel_inputs, amodel_inputs["metadata"])
                meta = m.set_metadata("ModelMetadata")
                amodel_inputs["metadata"] = m.get_metadata("ModelMetadata")
            if amodel_inputs:
                return Response(amodel_inputs, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        amodel_inputs = request.data.dict()
        serializer = self.serializer_class(data=request.data.dict(), context={'request': request})
        if serializer.is_valid() and pk is not None:
            try:
                original_amodel = AnalyticalModel.objects.get(id=int(pk))
            except AnalyticalModel.DoesNotExist:
                return Response(
                    "No analytical model found for id: {}".format(pk),
                    status=status.HTTP_400_BAD_REQUEST
                )
            if IsOwnerOfWorkflowChild().has_object_permission(request, self, original_amodel):
                amodel = serializer.update(original_amodel, serializer.validated_data)
                if amodel:
                    response_status = status.HTTP_201_CREATED
                    response_data = serializer.data
                    response_data["id"] = amodel.id
                    if int(pk) == amodel.id:
                        response_status = status.HTTP_200_OK
                    if "metadata" in amodel_inputs.keys():
                        amodel_inputs["metadata"] = None
                        m = Metadata(amodel_inputs, amodel_inputs["metadata"])
                        meta = m.set_metadata("ModelMetadata")
                        response_data["metadata"] = m.get_metadata("ModelMetadata")
                    return Response(response_data, status=response_status)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        if pk is not None:
            try:
                amodel = AnalyticalModel.objects.get(id=int(pk))
            except AnalyticalModel.DoesNotExist:
                return Response("No analytical model found for id: {}".format(pk), status=status.HTTP_400_BAD_REQUEST)
            if IsOwnerOfWorkflowChild().has_object_permission(request, self, amodel):
                amodel.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response("No analytical model 'id' in request.", status=status.HTTP_400_BAD_REQUEST)
