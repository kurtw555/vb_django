from rest_framework import viewsets, status, views
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from vb_django.models import Dataset
from vb_django.serializers import DatasetSerializer
from vb_django.permissions import IsOwnerOfWorkflowChild
from io import StringIO
import pandas as pd


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
        if 'workflow_id' in self.request.query_params.keys():
            a_models = Dataset.objects.filter(workflow_id=int(self.request.query_params.get('workflow_id')))
            serializer = self.serializer_class(a_models, many=True)
            for d in serializer.data:
                m = Dataset.objects.get(id=d["id"])
                d["data"] = pd.read_csv(StringIO(m.data.decode()))
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(
            "Required 'workflow_id' parameter for the workflow id was not found.",
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
                d = Dataset.objects.get(id=dataset["id"])
                dataset["data"] = pd.read_csv(StringIO(d.data.decode()))
                return Response(dataset, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        serializer = self.serializer_class(data=request.data.dict(), context={'request': request})
        if serializer.is_valid() and pk is not None:
            try:
                original_dataset = Dataset.objects.get(id=int(pk))
            except Dataset.DoesNotExist:
                return Response(
                    "No dataset model found for id: {}".format(pk),
                    status=status.HTTP_400_BAD_REQUEST
                )
            if IsOwnerOfWorkflowChild().has_object_permission(request, self, original_dataset):
                amodel = serializer.update(original_dataset, serializer.validated_data)
                if amodel:
                    response_status = status.HTTP_201_CREATED
                    response_data = serializer.data
                    response_data["id"] = amodel.id
                    response_data["data"] = pd.read_csv(StringIO(amodel.data.decode()))
                    if int(pk) == amodel.id:
                        response_status = status.HTTP_200_OK
                    return Response(response_data, status=response_status)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        if pk is not None:
            try:
                dataset = Dataset.objects.get(id=int(pk))
            except Dataset.DoesNotExist:
                return Response("No dataset found for id: {}".format(pk), status=status.HTTP_400_BAD_REQUEST)
            if IsOwnerOfWorkflowChild().has_object_permission(request, self, dataset):
                dataset.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response("No dataset 'id' in request.", status=status.HTTP_400_BAD_REQUEST)
