from rest_framework import generics, permissions
from .models import Client
from .serializers import ClientSerializer

class ClientListCreateView(generics.ListCreateAPIView):
    queryset = Client.objects.all().order_by("name")
    serializer_class = ClientSerializer

class ClientDetailView(generics.RetrieveAPIView):
    queryset = Client.objects.all()
    serializer_class = ClientSerializer
    permission_classes = [permissions.IsAuthenticated]
