from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated

from schools.models import Branch, BranchAdmin, School
from schools.api.serializers import BranchAdminSerializer, BranchSerializer, SchoolSerializer

class SchoolViewSet(viewsets.ModelViewSet):
    queryset = School.objects.all()
    serializer_class = SchoolSerializer
    permission_classes = [IsAuthenticated]

class BranchViewSet(viewsets.ModelViewSet):
    queryset = Branch.objects.all()
    serializer_class = BranchSerializer
    permission_classes = [IsAuthenticated]

class BranchAdminViewSet(viewsets.ModelViewSet):
    queryset = BranchAdmin.objects.all()
    serializer_class = BranchAdminSerializer
    permission_classes = [IsAuthenticated]
