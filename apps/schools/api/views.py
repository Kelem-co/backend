from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from schools.models import School
from schools.api.serializers import SchoolSerializer

class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]
