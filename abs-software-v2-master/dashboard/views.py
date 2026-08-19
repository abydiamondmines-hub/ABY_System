from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAdminUser, IsAuthenticated
from django.contrib.auth import get_user_model
from equipment.models import Equipment
from projects.models import Project
from incidents.models import Incident
from inventory.models import Inventory
from django.db.models import Count, Q, Sum
from django.utils.timezone import now
from safety.models import SafetyIncident, RiskAssessment
from finance.models import FinanceRecord
from rest_framework.generics import ListAPIView
from transaction.models import Transaction
from .serializers import TransactionSerializer
from operations.models import OperationRecord, MaintenanceRecord
from users.models import Employee
from django.db.models.functions import TruncDay, TruncMonth, TruncYear


from users.permissions import HasDashboardAccess

User = get_user_model()

class DashboardSummary(APIView):
    permission_classes = [HasDashboardAccess]

    def get(self, request):
        return Response({
            "users": User.objects.count(),
            "project_managers": User.objects.filter(role='project_manager').count(),
            "safety_officers": User.objects.filter(role='safety_officer').count(),
            "inventory_managers": User.objects.filter(role='inventory_manager').count(),
            "accounts_managers": User.objects.filter(role='accounts_manager').count(),
            "equipment_managers": User.objects.filter(role='equipment_manager').count(),
            "equipments": Equipment.objects.count(),
            "projects": Project.objects.count(),
            "incidents": Incident.objects.count(),
            "inventory": Inventory.objects.count(),
            "operation_records": OperationRecord.objects.count(),
            "maintenance_records": MaintenanceRecord.objects.count()
        })
class OperationalSummary(APIView):
    permission_classes = [HasDashboardAccess]

    def get(self, request):
        daily = OperationRecord.objects.annotate(day=TruncDay('date')) \
            .values('day') \
            .annotate(count=Count('id')) \
            .order_by('day')

        monthly = OperationRecord.objects.annotate(month=TruncMonth('date')) \
            .values('month') \
            .annotate(count=Count('id')) \
            .order_by('month')

        yearly = OperationRecord.objects.annotate(year=TruncYear('date')) \
            .values('year') \
            .annotate(count=Count('id')) \
            .order_by('year')

        return Response({
            "daily": list(daily),
            "monthly": list(monthly),
            "yearly": list(yearly)
        })
class MaintenanceSummary(APIView):
    permission_classes = [HasDashboardAccess]

    def get(self, request):
        daily = MaintenanceRecord.objects.annotate(day=TruncDay('date')) \
            .values('day') \
            .annotate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='completed')),
                pending=Count('id', filter=Q(status='pending'))
            ) \
            .order_by('day')

        monthly = MaintenanceRecord.objects.annotate(month=TruncMonth('date')) \
            .values('month') \
            .annotate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='completed')),
                pending=Count('id', filter=Q(status='pending'))
            ) \
            .order_by('month')

        yearly = MaintenanceRecord.objects.annotate(year=TruncYear('date')) \
            .values('year') \
            .annotate(
                total=Count('id'),
                completed=Count('id', filter=Q(status='completed')),
                pending=Count('id', filter=Q(status='pending'))
            ) \
            .order_by('year')

        return Response({
            "daily": list(daily),
            "monthly": list(monthly),
            "yearly": list(yearly)
        })
        
class RecentActivityFeed(APIView):
    permission_classes = [IsAuthenticated]

    def _fmt_user(self, user):
        """Return a clean display string for a user or None."""
        if user is None:
            return "System"
        name = f"{user.first_name} {user.last_name}".strip()
        return f"{name} ({user.email})" if name else user.email

    def get(self, request):
        activities = []
        entry_id = 0  # Synthetic incrementing id for stable sort

        # ── Projects ──────────────────────────────────────────
        for obj in Project.objects.order_by('-created_at')[:5]:
            entry_id += 1
            activities.append({
                "id": entry_id,
                "app_name": "projects",
                "model_name": "Project",
                "action": "added",
                "description": f"{obj.project_name} | Status: {obj.status}",
                "user": self._fmt_user(obj.user),
                "created_at": obj.created_at.isoformat(),
            })

        # ── Safety Incidents ───────────────────────────────────
        for obj in SafetyIncident.objects.order_by('-created_at')[:5]:
            entry_id += 1
            activities.append({
                "id": entry_id,
                "app_name": "safety",
                "model_name": "Safety Incident",
                "action": "reported",
                "description": f"{obj.description[:80]}" if obj.description else "No details",
                "user": self._fmt_user(obj.reported_by),
                "created_at": obj.created_at.isoformat(),
            })

        # ── Risk Assessments ───────────────────────────────────
        for obj in RiskAssessment.objects.order_by('-created_at')[:5]:
            entry_id += 1
            activities.append({
                "id": entry_id,
                "app_name": "safety",
                "model_name": "Risk Assessment",
                "action": "added",
                "description": f"{obj.project} — {obj.hazard_type} | Status: {obj.status}",
                "user": self._fmt_user(obj.assessed_by),
                "created_at": obj.created_at.isoformat(),
            })

        # ── Operations ─────────────────────────────────────────
        for obj in OperationRecord.objects.order_by('-timestamp')[:5]:
            entry_id += 1
            activities.append({
                "id": entry_id,
                "app_name": "production",
                "model_name": "Operation Record",
                "action": "added",
                "description": f"Date: {obj.date} | Income: {obj.income:,} | Expenditure: {obj.expenditure:,}",
                "user": self._fmt_user(getattr(obj, 'created_by', None)),
                "created_at": obj.timestamp.isoformat(),
            })

        # ── Maintenance ────────────────────────────────────────
        for obj in MaintenanceRecord.objects.order_by('-date')[:5]:
            entry_id += 1
            desc = obj.description[:80] if obj.description else "No details"
            activities.append({
                "id": entry_id,
                "app_name": "production",
                "model_name": "Maintenance Record",
                "action": "added",
                "description": desc,
                "user": self._fmt_user(getattr(obj, 'created_by', None)),
                "created_at": obj.date.isoformat() if obj.date else now().isoformat(),
            })

        # ── Inventory ──────────────────────────────────────────
        for obj in Inventory.objects.order_by('-updated_at')[:5]:
            entry_id += 1
            activities.append({
                "id": entry_id,
                "app_name": "inventory",
                "model_name": "Inventory Item",
                "action": "updated",
                "description": f"{obj.item_name} | Qty: {obj.quantity} {obj.unit} | Status: {obj.status}",
                "user": self._fmt_user(getattr(obj, 'user', None)),
                "created_at": obj.updated_at.isoformat(),
            })

        # ── Equipment ──────────────────────────────────────────
        for obj in Equipment.objects.order_by('-updated_at')[:5]:
            entry_id += 1
            activities.append({
                "id": entry_id,
                "app_name": "equipment",
                "model_name": "Equipment",
                "action": "updated",
                "description": f"{obj.equipment_name} | Type: {obj.equipment_type} | Status: {obj.status}",
                "user": self._fmt_user(getattr(obj, 'created_by', None)),
                "created_at": obj.updated_at.isoformat(),
            })

        # ── Employees ──────────────────────────────────────────
        for obj in Employee.objects.order_by('-updated_at')[:5]:
            entry_id += 1
            activities.append({
                "id": entry_id,
                "app_name": "user",
                "model_name": "Employee",
                "action": "updated",
                "description": f"{obj.name} | Rank: {obj.rank}",
                "user": "Admin",
                "created_at": obj.updated_at.isoformat(),
            })

        # ── User Category (System Users) ───────────────────────
        for obj in User.objects.order_by('-date_joined')[:5]:
            entry_id += 1
            name = f"{obj.first_name} {obj.last_name}".strip() or obj.username
            role_name = obj.role.name if obj.role else "No Role"
            activities.append({
                "id": entry_id,
                "app_name": "user",
                "model_name": "System User",
                "action": "added",
                "description": f"{name} | Role: {role_name} | {obj.email}",
                "user": self._fmt_user(obj),
                "created_at": obj.date_joined.isoformat(),
            })

        # Sort everything by created_at descending, take top 20
        activities.sort(key=lambda x: x['created_at'], reverse=True)
        return Response(activities[:20])
    
class FinancialSummary(APIView):
    permission_classes = [HasDashboardAccess]

    def get(self, request):
        revenue = FinanceRecord.objects.filter(type='revenue').aggregate(total=Sum('amount'))['total'] or 0
        expenses = FinanceRecord.objects.filter(type='expense').aggregate(total=Sum('amount'))['total'] or 0
        profit = revenue - expenses

        return Response({
            "revenue": revenue,
            "expenses": expenses,
            "profit": profit
        })
        
class InventoryStatus(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        total = Inventory.objects.count()
        status_counts = {
            "good": Inventory.objects.filter(status='good').count(),
            "average": Inventory.objects.filter(status='average').count(),
            "critical": Inventory.objects.filter(status='critical').count(),
        }

        return Response({
            "total": total,
            "status": status_counts
        })
        
class TransactionListView(ListAPIView):
    queryset = Transaction.objects.all()
    serializer_class = TransactionSerializer
    permission_classes = [IsAuthenticated]