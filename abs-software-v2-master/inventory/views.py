from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.views import APIView
from rest_framework.response import Response
from django.db.models import Sum, F
from .models import Inventory
from .serializers import InventorySerializer
from users.permissions import HasModulePermission

class InventoryListCreateView(generics.ListCreateAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [HasModulePermission]
    required_app = 'inventory'

class InventoryDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializer
    permission_classes = [HasModulePermission]
    required_app = 'inventory'
    lookup_field = 'id'

class InventorySummaryView(APIView):
    permission_classes = [HasModulePermission]
    required_app = 'inventory'

    def get(self, request):
        total_items = Inventory.objects.count()
        in_stock = Inventory.objects.filter(status='in_stock').count()
        restocking = Inventory.objects.filter(status='restocking').count()
        low_stock = Inventory.objects.filter(status='low_stock').count()

        return Response({
            "total_items": total_items,
            "in_stock": in_stock,
            "restocking": restocking,
            "low_stock": low_stock
        })
