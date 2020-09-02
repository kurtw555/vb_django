from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
from rest_framework.decorators import action
from vb_django.models import Workflow, Dataset, PreProcessingConfig, AnalyticalModel
from vb_django.serializers import WorkflowSerializer
from vb_django.permissions import IsOwnerOfLocationChild
from vb_django.app.preprocessing import PPGraph
from vb_django.task_controller import DaskTasks
from vb_django.app.metadata import Metadata
from django.core.exceptions import ObjectDoesNotExist
from io import StringIO
import pandas as pd
import json


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

    @action(detail=True, methods=["get"], name="Execute Pre-processing")
    def run_preprocessing(self, request, pk=None):
        """
        Execute a preprocessing configuration on a specified dataset.
        :param request: GET request containing two parameters dataset_id and preprocessing_id
        :param pk: id of the workflow
        :return: complete pre-processing transformation of the dataset
        """
        if "dataset_id" in self.request.query_params.keys():
            try:
                dataset = Dataset.objects.get(id=int(self.request.query_params.get('dataset_id')))
            except Dataset.DoesNotExist:
                return Response("No dataset found for id: {}".format(int(self.request.query_params.get('dataset_id'))),
                                status=status.HTTP_400_BAD_REQUEST)
            if "preprocessing_id" in self.request.query_params.keys():
                try:
                    preprocess_config = PreProcessingConfig.objects.get(
                        id=int(self.request.query_params.get('preprocessing_id'))
                    )
                except PreProcessingConfig.DoesNotExist:
                    return Response(
                        "No preprocessing configuration found for id: {}".format(
                            int(self.request.query_params.get('preprocessing_id'))),
                        status=status.HTTP_400_BAD_REQUEST
                    )
                raw_data = pd.read_csv(StringIO(dataset.data.decode()))
                pp_configuration = json.loads(preprocess_config.config)
                result_string = StringIO()
                result = PPGraph(raw_data, pp_configuration).data
                result_columns = set.difference(set(result.columns), set(raw_data.columns))
                result = result[result_columns]
                result.to_csv(result_string)
                response_result = {"processed_data": result}
                return Response(response_result, status=status.HTTP_200_OK)
            else:
                return Response("No preprocessing 'preprocessing_id' in request.", status=status.HTTP_400_BAD_REQUEST)
        else:
            return Response("No dataset 'dataset_id' in request.", status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=["post"], name="Execute technique for specified dataset, analytical model and preprocessing")
    def execute(self, request):
        input_data = request.data.dict()
        required_parameters = ["workflow_id", "dataset_id", "model_id"]
        if set(required_parameters).issubset(input_data.keys()):
            try:
                workflow = Workflow.objects.get(id=int(input_data["workflow_id"]))
            except ObjectDoesNotExist:
                workflow = None
            try:
                amodel = AnalyticalModel.objects.get(id=int(input_data["model_id"]))
            except ObjectDoesNotExist:
                amodel = None
            try:
                dataset = Dataset.objects.get(id=int(input_data["dataset_id"]))
            except ObjectDoesNotExist:
                dataset = None
            if workflow is None or dataset is None or amodel is None:
                message = []
                if workflow is None:
                    message.append("No workflow found for id: {}".format(input_data["workflow_id"]))
                if dataset is None:
                    message.append("No dataset found for id: {}".format(input_data["dataset_id"]))
                if amodel is None:
                    message.append("No analytical model found for id: {}".format(input_data["model_id"]))
                return Response(", ".join(message), status=status.HTTP_400_BAD_REQUEST)
            elif IsOwnerOfLocationChild().has_object_permission(request, self, workflow):
                try:
                    DaskTasks.setup_task(dataset_id=dataset.id, amodel_id=amodel.id)
                    response = "Successfully executed analytical model"
                except Exception as ex:
                    response = "Error occured attempting to execute analytical model. Message: {}".format(ex)
                return Response(response, status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        else:
            return Response(
                "Missing required parameters in POST request. Required parameters: {}".format(", ".join(required_parameters)),
                status.HTTP_400_BAD_REQUEST
            )

    @action(detail=False, methods=["POST"], name="Get the status/results of an executed task.")
    def data(self, request):
        inputs = request.data.dict()
        required_parameters = ["workflow_id", "model_id"]
        if set(required_parameters).issubset(inputs.keys()):
            try:
                workflow = Workflow.objects.get(id=int(inputs["workflow_id"]))
            except ObjectDoesNotExist:
                workflow = None
            try:
                amodel = AnalyticalModel.objects.get(id=int(inputs["model_id"]))
            except ObjectDoesNotExist:
                amodel = None
            if workflow is None or amodel is None:
                message = []
                message = message if workflow else message.append("No workflow found for id: {}".format(inputs["workflow_id"]))
                message = message if amodel else message.append("No analytical model found for id: {}".format(inputs["amodel_id"]))
                return Response(",".join(message), status=status.HTTP_400_BAD_REQUEST)
            elif IsOwnerOfLocationChild().has_object_permission(request, self, workflow):
                response = {}
                if amodel.model:
                    data = None
                    if "data" in inputs.keys():
                        data = pd.read_csv(StringIO(inputs["data"]))
                    response["data"] = DaskTasks.make_prediction(amodel.id, data)
                    response["dataset_id"] = amodel.dataset
                meta = Metadata(parent=amodel)
                metadata = meta.get_metadata("ModelMetadata", ['status', 'stage', 'message'])
                response["metadata"] = metadata
                response["analytical_model_id"] = amodel.id
                response["workflow_id"] = workflow.id
                return Response(response, status=status.HTTP_200_OK)
        data = "Missing required parameters: {}".format(", ".join(required_parameters))
        response_status = status.HTTP_200_OK
        return Response(data, status=response_status)
