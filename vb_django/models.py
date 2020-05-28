from django.db import models
from django.contrib.auth.models import User


class Location(models.Model):
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    name = models.CharField(max_length=64)
    description = models.CharField(max_length=128)
    start_latitude = models.FloatField(max_length=12)
    start_longitude = models.FloatField(max_length=12)
    end_latitude = models.FloatField(max_length=12)
    end_longitude = models.FloatField(max_length=12)
    o_latitude = models.FloatField(max_length=12)
    o_longitude = models.FloatField(max_length=12)


class LocationMetadata(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    value = models.CharField(max_length=128)


class Workflow(models.Model):
    location = models.ForeignKey(Location, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=128)


class WorkflowResults(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    dataset = models.CharField(max_length=32)           # ModelData ID
    timestamp = models.DateTimeField()
    comments = models.CharField(max_length=256)


class AnalyticalModel(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=128)
    variables = models.CharField(max_length=256, null=True, blank=True)        # serializable JSON
    model = models.BinaryField(null=True, blank=True)
    dataset = models.CharField(max_length=16, null=True, blank=True)


class ModelMetadata(models.Model):
    model = models.ForeignKey(AnalyticalModel, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    value = models.CharField(max_length=128)


class ModelData(models.Model):
    model = models.ForeignKey(AnalyticalModel, on_delete=models.CASCADE)
    dataset = models.CharField(max_length=32)           # dataset ID
    name = models.CharField(max_length=32)
    data = models.BinaryField()
    comments = models.CharField(max_length=256)


class ModelResults(models.Model):
    model = models.ForeignKey(AnalyticalModel, on_delete=models.CASCADE)
    dataset = models.CharField(max_length=32)   # dataset ID
    timestamp = models.DateTimeField()
    result = models.FloatField()


class Dataset(models.Model):
    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    description = models.CharField(max_length=128)
    data = models.BinaryField()


class DatasetMetadata(models.Model):
    model = models.ForeignKey(Dataset, on_delete=models.CASCADE)
    name = models.CharField(max_length=32)
    value = models.CharField(max_length=128)


class AccessControlList(models.Model):
    types = (
        ('Location', 'Location'),
        ('Workflow', 'Workflow'),
        ('AnalyticalModel', 'AnalyticalModel'),
        ('Dataset', 'Dataset')
    )
    a_types = (
        ('Read', 'Read'),
        ('Write', 'Write')
    )
    owner = models.ForeignKey(User, on_delete=models.CASCADE)
    target_user = models.CharField(max_length=32)
    object_id = models.CharField(max_length=32)
    object_type = models.CharField(max_length=15, choices=types)
    expiration = models.DateTimeField()
    access_type = models.CharField(max_length=5, choices=a_types)
