from rest_framework import viewsets
from students.models import Student, ParentStudentLink
from .serializers import (
    StudentSerializer, 
    ParentStudentLinkSerializer, 
    ParentStudentLinkReadSerializer
)

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = "id"

class ParentStudentLinkViewSet(viewsets.ModelViewSet):
    queryset = ParentStudentLink.objects.select_related("student", "parent").all()
    lookup_field = "id"

    def get_serializer_class(self):
        if self.action in ["list", "retrieve"]:
            return ParentStudentLinkReadSerializer
        return ParentStudentLinkSerializer
