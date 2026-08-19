from django.shortcuts import render
from rest_framework import viewsets, views, permissions
from rest_framework.response import Response
from .models import Project
from .serializers import ProjectSerializer
from users.permissions import HasModulePermission

class ProjectViewSet(viewsets.ModelViewSet):
    queryset = Project.objects.all().order_by('-created_at')
    serializer_class = ProjectSerializer
    permission_classes = [HasModulePermission]
    required_app = 'projects'

class ProjectStatsView(views.APIView):
    permission_classes = [HasModulePermission]
    required_app = 'projects'

    def get(self, request):
        total = Project.objects.count()
        active = Project.objects.filter(status='active').count()
        completed = Project.objects.filter(status='completed').count()
        delayed = Project.objects.filter(status='delayed').count()
        cancelled = Project.objects.filter(status='cancelled').count()
        return Response({
            "total_projects": total,
            "active_projects": active,
            "completed_projects": completed,
            "delayed_projects": delayed,
            "cancelled_projects": cancelled
        })

