from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import api_view
from rest_framework.authentication import TokenAuthentication
from drf_yasg.utils import swagger_auto_schema
from vb_django.models import Location
from vb_django.serializers import LocationSerializer
from vb_django.permissions import IsOwner


class LocationView(viewsets.ViewSet):
    """
    The Location API endpoint viewset for managing user locations in the database.
    """
    serializer_class = LocationSerializer
    authentication_classes = [TokenAuthentication]
    permission_classes = [IsAuthenticated, IsOwner]

    def list(self, request):
        """
        GET request that lists all the locations owned by the user.
        :param request: GET request
        :return: List of locations
        """
        locations = Location.objects.filter(owner_id=request.user)
        # TODO: Add ACL access objects
        serializer = self.serializer_class(locations, many=True)
        return Response(serializer.data, status=status.HTTP_200_OK)

    def create(self, request):
        """
        POST request that creates a new location.
        :param request: POST request
        :return: New location object
        """
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid():
            location = serializer.save()
            if location:
                return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, pk=None):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid() and pk is not None:
            try:
                original_location = Location.objects.get(id=int(pk))
            except Location.DoesNotExist:
                return Response("No location found for id: {}".format(pk), status=status.HTTP_400_BAD_REQUEST)
            if IsOwner().has_object_permission(request, self, original_location):
                location = serializer.update(original_location, serializer.validated_data)
                if location:
                    request_status = status.HTTP_201_CREATED
                    if int(pk) == location.id:
                        request_status = status.HTTP_200_OK
                    return Response(serializer.data, status=request_status)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def destroy(self, request, pk=None):
        # pk = args['location_id']
        if pk is not None:
            try:
                location = Location.objects.get(id=int(pk))
            except Location.DoesNotExist:
                return Response("No location found for id: {}".format(pk), status=status.HTTP_400_BAD_REQUEST)
            if IsOwner().has_object_permission(request, self, location):
                location.delete()
                return Response(status=status.HTTP_200_OK)
            else:
                return Response(status=status.HTTP_401_UNAUTHORIZED)
        return Response("No location 'id' in request.", status=status.HTTP_400_BAD_REQUEST)
