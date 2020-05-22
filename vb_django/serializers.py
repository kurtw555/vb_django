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
    owner = serializers.PrimaryKeyRelatedField(read_only=True, default=serializers.CurrentUserDefault())

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
            location.owner = self.context["request"].user
            location.save()
        return location

    def update(self, instance, validated_data):
        location = instance
        validated = self.validate_points(validated_data)
        if validated:
            can_update = self.check_integrity(instance)
            if can_update:
                location = vb_models.Location(**validated_data)
                location.owner = self.context["request"].user
                location.id = instance.id
                location.save()
            else:
                location = vb_models.Location(**validated_data)
                location.owner = self.context["request"].user
                location.save()
        return location

    class Meta:
        model = vb_models.Location
        fields = [
            "id", "owner", "name", "description",
            "start_latitude", "start_longitude",
            "end_latitude", "end_longitude",
            "o_latitude", "o_longitude"
        ]


class LocationMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.LocationMetadata
        fields = [
            "location", "name", "value"
        ]


class WorkflowSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = [
            "location", "name", "description"
        ]


class WorkflowResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = [
            "workflow", "dataset", "timestamp", "comments"
        ]


class AnalyticalModelSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = [
            "workflow", "name", "description", "variables", "model", "dataset"
        ]


class ModelMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = [
            "model", "name", "value"
        ]


class ModelDataSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = ["model", "dataset", "name", "data", "comments"]


class ModelResultsSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = [
            "model", "dataset", "timestamp", "result"
        ]


class DatasetSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = [
            "workflow", "name", "description", "data"
        ]


class DatasetMetadataSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = [
            "model", "name", "value"
        ]


class AccessControlListSerializer(serializers.ModelSerializer):
    class Meta:
        model = vb_models.Location
        fields = [
            "owner", "target_user", "object_id", "object_type", "expiration", "access_type"
        ]
