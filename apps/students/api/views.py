from rest_framework import viewsets
from students.models import Student, ParentStudentLink
from .serializers import StudentSerializer, ParentStudentLinkSerializer

class StudentViewSet(viewsets.ModelViewSet):
    queryset = Student.objects.all()
    serializer_class = StudentSerializer
    lookup_field = "id"

class ParentStudentLinkViewSet(viewsets.ModelViewSet):
    queryset = ParentStudentLink.objects.all()
    serializer_class = ParentStudentLinkSerializer
    lookup_field = "id"
