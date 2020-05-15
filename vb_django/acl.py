from vb_django.models import Location, Workflow, Dataset, AnalyticalModel, AccessControlList
import datetime


class Authorization:
    """
    Authorization performs an ownership check of the resource and permissions check from the ACL.
    TODO: ACL check currently not implemented.
    """

    def grant_access(self, user, target_user, object_type, object_id, expiration, access_type="READ"):
        """
        Add entry in the ACL for the specific object and target user.
        :param user: The current user (must be owner of the object)
        :param target_user: The target user who access is being given to
        :param object_type:
        :param object_id:
        :param expiration:
        :param access_type:
        :return:
        """
        owner = self.get_owner(object_type, object_id)
        if owner is None or owner != user:
            return False
        current_acl = AccessControlList.objects.filter(
            owner=user,
            target_user=target_user,
            object_type=object_type,
            object_id=object_id
        )
        if current_acl is None:
            new_acl = AccessControlList(
                owner=user,
                access_type=access_type,
                object_id=object_id,
                target_user=target_user,
                expiration=expiration
            )
            new_acl.save()
        else:
            current_acl.expiration = expiration
            current_acl.access_type = access_type
            current_acl.save()
        return True

    def get_owner(self, object_type, object_id):
        """
        Gets the owner of the object if the object type and id is valid.
        :param object_type: Type of object
        :param object_id: The ID of the object
        :return: The owner of the object or None if the object does not exist
        """
        if object_type == "Location":
            l = Location.objects.filter(id=object_id)
            if l is not None:
                return l.owner
            else:
                return None
        elif object_type == "Workflow":
             w = Workflow.objects.filter(id=object_id)
             if w is not None:
                 return w.location.owner
             else:
                return None
        elif object_type == "Dataset":
            d = Dataset.objects.filter(id=object_id)
            if d is not None:
                return d.workflow.location.owner
            else:
                return None
        elif object_type == "AnalyticalModel":
            am = AnalyticalModel.objects.filter(id=object_id)
            if am is not None:
                return am.workflow.location.owner
            else:
                return None
        return None

    def check_authorization(self, user, object_type, object_id):
        """
        Base function for authorization check
        :param user: The current user
        :param object_type: The type of resource/object being requested
        :param object_id: The id of the requested resource
        :return: True if the user has access to the resource or False if access is denied
        """
        if object_type == "Location":
            return self.check_location(user, object_id)
        elif object_type == "Workflow":
            return self.check_workflow(user, object_id)
        elif object_type == "Dataset":
            return self.check_dataset(user, object_id)
        elif object_type == "AnalyticalModel":
            return self.check_analyticalmodel(user, object_id)
        else:
            return False

    def check_location(self, user, id):
        """
        Run authorization check on the Location resource
        :param user: Current user
        :param id: Location ID
        :return: True if user has access, False if denied access.
        """
        has_access = False
        location = Location.objects.filter(id=id)
        if location.owner == user:
            has_access = True
        location_acl = AccessControlList.objects.filter(target_user=user.id, object_type="Location", object_id=id)
        # if location_acl is not None:
            # current_dt = datetime.datetime.now()
            # TODO: Add expiration check, if expiration is < than now() deny access and remove entry from ACL
            # has_access = True
        return has_access

    def check_workflow(self, user, id):
        """
        Run authorization check on the Workflow resource
        :param user: Current user
        :param id: Workflow ID
        :return: True if user has access, False if denied access
        """
        has_access = False
        workflow = Workflow.objects.filter(id=id)
        if workflow.location.owner == user:
            has_access = True
        workflow_acl = AccessControlList.objects.filter(target_user=user.id, object_type="Workflow", object_id=id)
        # if workflow_acl is not None:
            # current_dt = datetime.datetime.now()
            # TODO: Add expiration check, if expiration is < than now() deny access and remove entry from ACL
            # has_access = True
        return has_access

    def check_dataset(self, user, id):
        """
        Run authorization check on the Dataset resource
        :param user: Current user
        :param id: Dataset ID
        :return: True if user has access, False if denied access
        """
        has_access = False
        dataset = Dataset.objects.filter(id=id)
        if dataset.workflow.location.owner == user:
            has_access = True
        dataset_acl = AccessControlList.objects.filter(target_user=user.id, object_type="Dataset", object_id=id)
        # if dataset_acl is not None:
            # current_dt = datetime.datetime.now()
            # TODO: Add expiration check, if expiration is < than now() deny access and remove entry from ACL
            # has_access = True
        return has_access

    def check_analyticalmodel(self, user, id):
        """
        Run authorization check on the Analytical Model resource
        :param user: Current user
        :param id: Analytical model ID
        :return: True if user has access, False if denied access
        """
        has_access = False
        am = AnalyticalModel.objects.filter(id=id)
        if am.workflow.location.owner == user:
            has_access = True
        am_acl = AccessControlList.objects.filter(target_user=user.id, object_type="AnalyticalModel", object_id=id)
        # if dataset_acl is not None:
            # current_dt = datetime.datetime.now()
            # TODO: Add expiration check, if expiration is < than now() deny access and remove entry from ACL
            # has_access = True
        return has_access

