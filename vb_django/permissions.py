from rest_framework import permissions
from vb_django.models import AnalyticalModel, Workflow, Location


class IsOwner(permissions.BasePermission):
    """
    Checks if the user ia the owner of the object.
    """
    def has_object_permission(self, request, view, obj):
        return obj.owner_id == request.user


class IsOwnerOfLocationChild(permissions.BasePermission):
    """
    Checks if the user ia the owner of the workflow's corresponding location.
    """
    def has_object_permission(self, request, view, obj):
        return obj.location_id.owner_id == request.user


class IsOwnerOfWorkflowChild(permissions.BasePermission):
    """
    Checks if the user ia the owner of the analytical model's corresponding location.
    """
    def has_object_permission(self, request, view, obj):
        return obj.workflow_id.location_id.owner_id == request.user


class HasModelIntegrity(permissions.BasePermission):
    """
    Checks if the object has been used for creating a model, where an update would degrade the integrity of the workflow
    """
    def has_object_permission(self, request, view, obj):
        existing_model = False
        models = AnalyticalModel.objects.filter(workflow__location__id=obj.id)
        for m in models:
            if m.model is not None:
                existing_model = True
        return existing_model
