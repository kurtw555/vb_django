from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from vb_django.models import Dataset
from vb_django.serializers import DatasetSerializer
from vb_django.permissions import IsOwnerOfWorkflowChild


class DatasetView(viewsets.ViewSet):
    """
    The Dataset API endpoint viewset for managing user datasets in the database.
    """
    serializer_class = DatasetSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwnerOfWorkflowChild]

    def list(self, request, pk=None):
        """
        GET request that lists all the Datasets for a specific workflow id
        :param request: GET request, containing the workflow id as 'workflow'
        :return: List of datasets
        """
        if 'workflow' in self.request.query_params.keys():
            a_models = Dataset.objects.filter(workflow__id=int(self.request.query_params.get('workflow')))
            serializer = self.serializer_class(a_models, many=True)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            "Required 'workflow' parameter for the workflow id was not found.",
            status=status.HTTP_400_BAD_REQUEST
        )

    def create(self, request):
        """
        POST request that creates a new Dataset.
        :param request: POST request
        :return: New dataset
        """
        dataset_inputs = request.data.dict()
        serializer = self.serializer_class(data=dataset_inputs, context={'request': request})
        if serializer.is_valid():
            serializer.save()
            dataset = serializer.data
            if dataset:
                return Response(dataset, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def put(self, request):
        serializer = self.serializer_class(data=request.data.dict(), context={'request': request})
        if serializer.is_valid() and "id" in request.data.keys():
            try:
                original_dataset = Dataset.objects.get(id=request.data["id"])
            except Dataset.DoesNotExist:
                return Response(
                    "No dataset model found for id: {}".format(request.data["id"]),
                    status=status.HTTP_400_BAD_REQUEST
                )
            if IsOwnerOfWorkflowChild().has_object_permission(request, self, original_dataset):
                amodel = serializer.update(original_dataset, serializer.validated_data)
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
                dataset = Dataset.objects.get(id=request.data["id"])
            except Dataset.DoesNotExist:
                return Response("No dataset found for id: {}".format(request.data["id"]), status=status.HTTP_400_BAD_REQUEST)
            if IsOwnerOfWorkflowChild().has_object_permission(request, self, dataset):
                dataset.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response("No dataset 'id' in request.", status=status.HTTP_400_BAD_REQUEST)
