from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from vb_django.models import AnalyticalModel
from vb_django.serializers import AnalyticalModelSerializer
from vb_django.permissions import IsOwnerOfAnalyticalModel


class AnalyticalModelView(viewsets.ViewSet):
    """
    The Analytical Model API endpoint viewset for managing user analytical models in the database.
    """
    serializer_class = AnalyticalModelSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOfAnalyticalModel]

    def list(self, request, pk=None):
        """
        GET request that lists all the analytical models for a specific workflow id
        :param request: GET request, containing the workflow id as 'workflow'
        :return: List of analytical models
        """
        if 'workflow' in self.request.query_params.keys():
            a_models = AnalyticalModel.objects.filter(workflow__id=int(self.request.query_params.get('workflow')))
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
            if amodel_inputs:
                return Response(amodel_inputs, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        serializer = self.serializer_class(data=request.data.dict(), context={'request': request})
        if serializer.is_valid() and "id" in request.data.keys():
            try:
                original_amodel = AnalyticalModel.objects.get(id=request.data["id"])
            except AnalyticalModel.DoesNotExist:
                return Response(
                    "No analytical model found for id: {}".format(request.data["id"]),
                    status=status.HTTP_400_BAD_REQUEST
                )
            if IsOwnerOfAnalyticalModel().has_object_permission(request, self, original_amodel):
                amodel = serializer.update(original_amodel, serializer.validated_data)
                if amodel:
                    response_status = status.HTTP_201_CREATED
                    response_data = serializer.data
                    response_data["id"] = amodel.id
                    if int(request.data["id"]) == amodel.id:
                        response_status = status.HTTP_200_OK
                    return Response(response_data, status=response_status)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if "id" in request.data.keys():
            try:
                amodel = AnalyticalModel.objects.get(id=request.data["id"])
            except AnalyticalModel.DoesNotExist:
                return Response("No analytical model found for id: {}".format(request.data["id"]), status=status.HTTP_400_BAD_REQUEST)
            if IsOwnerOfAnalyticalModel().has_object_permission(request, self, amodel):
                amodel.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response("No workflow 'id' in request.", status=status.HTTP_400_BAD_REQUEST)
