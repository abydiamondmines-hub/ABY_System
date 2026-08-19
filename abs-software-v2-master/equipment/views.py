from rest_framework import generics, permissions
from rest_framework.views import APIView
from rest_framework.response import Response
from .models import Equipment
from .serializers import EquipmentSerializer
from users.permissions import HasModulePermission

class EquipmentListCreateView(generics.ListCreateAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [HasModulePermission]
    required_app = 'equipment'

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class EquipmentUpdateView(generics.UpdateAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [HasModulePermission]
    required_app = 'equipment'
    lookup_field = 'id'

class EquipmentDeleteView(generics.DestroyAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    permission_classes = [HasModulePermission]
    required_app = 'equipment'
    lookup_field = 'id'

class EquipmentDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Equipment.objects.all()
    serializer_class = EquipmentSerializer
    lookup_field = 'id'
    permission_classes = [HasModulePermission]
    required_app = 'equipment'

class EquipmentStatsView(APIView):
    permission_classes = [HasModulePermission]
    required_app = 'equipment'

    def get(self, request):
        total = Equipment.objects.count()
        available = Equipment.objects.filter(status__iexact='available').count()
        active = Equipment.objects.filter(status__iexact='active').count()
        repair = Equipment.objects.filter(status__iexact='repair').count()
        retired = Equipment.objects.filter(status__iexact='retired').count()

        return Response({
            "total_equipment": total,
            "available_equipment": available,
            "active_equipment": active,
            "repair_equipment": repair,
            "retired_equipment": retired
        })
