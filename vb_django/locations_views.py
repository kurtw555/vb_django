from rest_framework import viewsets, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.authentication import TokenAuthentication
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
        locations = Location.objects.filter(owner=request.user)
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

    def put(self, request):
        serializer = self.serializer_class(data=request.data, context={'request': request})
        if serializer.is_valid() and "id" in request.data.keys():
            try:
                original_location = Location.objects.get(id=request.data["id"])
            except Location.DoesNotExist:
                return Response("No location found for id: {}".format(request.data["id"]), status=status.HTTP_400_BAD_REQUEST)
            location = serializer.update(original_location, serializer.validated_data)
            if location:
                request_status = status.HTTP_201_CREATED
                if int(request.data["id"]) == location.id:
                    request_status = status.HTTP_200_OK
                return Response(serializer.data, status=request_status)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request):
        if "id" in request.data.keys():
            try:
                location = Location.objects.get(id=request.data["id"])
            except Location.DoesNotExist:
                return Response("No location found for id: {}".format(request.data["id"]), status=status.HTTP_400_BAD_REQUEST)
            location.delete()
            return Response(status=status.HTTP_200_OK)
        return Response("No location 'id' in request.", status=status.HTTP_400_BAD_REQUEST)
