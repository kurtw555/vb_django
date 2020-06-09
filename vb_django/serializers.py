from django.contrib.auth.models import User
from rest_framework import serializers
from rest_framework.validators import UniqueValidator
import vb_django.models as vb_models
from vb_django.validation import Validator


class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(
            required=True,
            validators=[UniqueValidator(queryset=User.objects.all())]
            )
    username = serializers.CharField(
            validators=[UniqueValidator(queryset=User.objects.all())]
            )
    password = serializers.CharField(min_length=8, write_only=True)

    def create(self, validated_data):
        user = User.objects.create_user(validated_data['username'], validated_data['email'], validated_data['password'])
        return user

    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'password']


class LocationSerializer(serializers.ModelSerializer):
    owner_id = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

    def validate_points(self, validated_data):
        validated = True
        if not Validator.validate_point(validated_data["start_latitude"], validated_data["start_longitude"]):
            self.errors["start_point"] = "Start point coordinates, start_latitude/start_longitude, are invalid"
            validated = False
        if not Validator.validate_point(validated_data["end_latitude"], validated_data["end_longitude"]):
            self.errors["end_point"] = "End point coordinates, end_latitude/end_longitude, are invalid"
            validated = False
        if not Validator.validate_point(validated_data["o_latitude"], validated_data["o_longitude"]):
            self.errors["o_point"] = "Orientation point coordinates, o_latitude/o_longitude, are invalid"
            validated = False
        return validated

    def check_integrity(self, location):
        can_update = True
        a_models = vb_models.AnalyticalModel.objects.filter(workflow__location__id=location.id)
        for m in a_models:
            if m.model is not None:
                can_update = False
        return can_update

    def create(self, validated_data):
        location = None
        validated = self.validate_points(validated_data)
        if validated:
            location = vb_models.Location(**validated_data)
            location.owner_id = self.context["request"].user
            location.save()
        return location

    def update(self, instance, validated_data):
        location = instance
        validated = self.validate_points(validated_data)
        if validated:
            can_update = self.check_integrity(instance)
            if can_update:
                location = vb_models.Location(**validated_data)
                location.owner_id = self.context["request"].user
                location.id = instance.id
                location.save()
            else:
                location = vb_models.Location(**validated_data)
                location.owner_id = self.context["request"].user
                location.save()
        return location

    class Meta:
        model = vb_models.Location
        fields = [
            "id", "owner_id", "name", "description",
            "start_latitude", "start_longitude",
            "end_latitude", "end_longitude",
            "o_latitude", "o_longitude"
        ]


class LocationMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.LocationMetadata
        fields = [
            "location_id", "name", "value"
        ]


class WorkflowSerializer(serializers.ModelSerializer):
    location_id = serializers.PrimaryKeyRelatedField(queryset=vb_models.Location.objects.all())

    def create(self, validated_data):
        workflow = vb_models.Workflow(**validated_data)
        workflow.save()
        return workflow

    def check_integrity(self, workflow):
        can_update = True
        a_models = vb_models.AnalyticalModel.objects.filter(workflow__id=workflow.id)
        for m in a_models:
            if m.model is not None:
                can_update = False
        return can_update

    def update(self, instance, validated_data):
        can_update = self.check_integrity(instance)
        workflow = vb_models.Workflow(**validated_data)
        if can_update:
            workflow.id = instance.id
        workflow.location = instance.location
        workflow.save()
        return workflow

    class Meta:
        model = vb_models.Workflow
        fields = [
            "id", "location_id", "name", "description"
        ]


class WorkflowResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.WorkflowResults
        fields = [
            "workflow_id", "dataset_id", "timestamp", "comments"
        ]


class PreProcessingConfigSerializer(serializers.ModelSerializer):

    class Meta:
        model = vb_models.PreProcessingConfig
        fields = ["workflow_id", "id", "name", "config"]


class AnalyticalModelSerializer(serializers.ModelSerializer):
    workflow_id = serializers.PrimaryKeyRelatedField(queryset=vb_models.Workflow.objects.all())

    def create(self, validated_data):
        amodel = vb_models.AnalyticalModel(**validated_data)
        amodel.save()
        return amodel

    def update(self, instance, validated_data):
        amodel = vb_models.AnalyticalModel(**validated_data)
        if instance.model is None:
            amodel.id = instance.id
        amodel.workflow = instance.workflow
        amodel.save()
        return amodel

    class Meta:
        model = vb_models.AnalyticalModel
        fields = [
            "id", "workflow_id", "name", "description", "variables", "dataset"
        ]


class ModelMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.ModelMetadata
        fields = [
            "model_id", "name", "value"
        ]


class ModelDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.ModelData
        fields = ["model_id", "dataset_id", "name", "data", "comments"]


class ModelResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.ModelResults
        fields = [
            "model_id", "dataset_id", "timestamp", "result"
        ]


class DatasetSerializer(serializers.ModelSerializer):
    workflow_id = serializers.PrimaryKeyRelatedField(queryset=vb_models.Workflow.objects.all())
    data = serializers.CharField()

    def check_integrity(self, workflow):
        can_update = True
        a_models = vb_models.AnalyticalModel.objects.filter(workflow_id=workflow.id)
        for m in a_models:
            if m.model is not None:
                can_update = False
        return can_update

    def create(self, validated_data):
        if "data" in validated_data.keys():
            validated_data["data"] = str(validated_data["data"]).encode()
        dataset = vb_models.Dataset(**validated_data)
        dataset.save()
        return dataset

    def update(self, instance, validated_data):
        if "data" in validated_data.keys():
            validated_data["data"] = str(validated_data["data"]).encode()
        dataset = vb_models.Dataset(**validated_data)
        if self.check_integrity(dataset.workflow_id):
            dataset.id = instance.id
        dataset.workflow_id = instance.workflow_id
        dataset.save()
        return dataset

    class Meta:
        model = vb_models.Dataset
        fields = [
            "id", "workflow_id", "name", "description", "data"
        ]


class DatasetMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.DatasetMetadata
        fields = [
            "model_id", "name", "value"
        ]


class AccessControlListSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.AccessControlList
        fields = [
            "owner_id", "target_user_id", "object_id", "object_type", "expiration", "access_type"
        ]
