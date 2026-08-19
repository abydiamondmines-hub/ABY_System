from rest_framework import viewsets, views, response
from .models import DailyProduction
from operations.models import OperationRecord, MaintenanceRecord
from .serializers import DailyProductionSerializer, OperationRecordSerializer, MaintenanceRecordSerializer
from django.db.models import Sum
from users.permissions import HasModulePermission

class DailyProductionViewSet(viewsets.ModelViewSet):
    queryset = DailyProduction.objects.all().order_by('-date', '-id')
    serializer_class = DailyProductionSerializer
    permission_classes = [HasModulePermission]
    required_app = 'production'

class OperationRecordViewSet(viewsets.ModelViewSet):
    queryset = OperationRecord.objects.all().order_by('-date', '-id')
    serializer_class = OperationRecordSerializer
    permission_classes = [HasModulePermission]
    required_app = 'operations'

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class MaintenanceRecordViewSet(viewsets.ModelViewSet):
    queryset = MaintenanceRecord.objects.all().order_by('-date', '-id')
    serializer_class = MaintenanceRecordSerializer
    permission_classes = [HasModulePermission]
    required_app = 'operations'

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class OperationSummaryView(views.APIView):
    permission_classes = [HasModulePermission]
    required_app = 'operations'
    def get(self, request):
        total_operations = OperationRecord.objects.count()
        total_hours = OperationRecord.objects.aggregate(total=Sum('hours_used'))['total'] or 0
        completed = OperationRecord.objects.filter(status='completed').count()
        pending = OperationRecord.objects.filter(status='pending').count()
        
        totals = OperationRecord.objects.aggregate(
            total_income=Sum('income'),
            total_expenditure=Sum('expenditure')
        )
        total_income = totals['total_income'] or 0
        total_expenditure = totals['total_expenditure'] or 0
        total_balance = total_income - total_expenditure

        return response.Response({
            "total_operations": total_operations,
            "total_hours": total_hours,
            "completed": completed,
            "pending": pending,
            "total_income": total_income,
            "total_expenditure": total_expenditure,
            "total_balance": total_balance
        })

class MaintenanceSummaryView(views.APIView):
    permission_classes = [HasModulePermission]
    required_app = 'operations'
    def get(self, request):
        total_maintenance = MaintenanceRecord.objects.count()
        completed = MaintenanceRecord.objects.filter(status='completed').count()
        pending = MaintenanceRecord.objects.filter(status='pending').count()

        totals = MaintenanceRecord.objects.aggregate(
            total_income=Sum('income'),
            total_expenditure=Sum('expenditure')
        )
        total_income = totals['total_income'] or 0
        total_expenditure = totals['total_expenditure'] or 0
        total_balance = total_income - total_expenditure

        return response.Response({
            "total_maintenance": total_maintenance,
            "completed": completed,
            "pending": pending,
            "total_income": total_income,
            "total_expenditure": total_expenditure,
            "total_balance": total_balance
        })
