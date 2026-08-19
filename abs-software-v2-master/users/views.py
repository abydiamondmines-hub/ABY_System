# ────────────────────────────────────────────────────────────────
# Imports
# ────────────────────────────────────────────────────────────────

import random
import logging
from django.contrib.auth import authenticate, get_user_model, login

logger = logging.getLogger(__name__)
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_decode
from django.contrib.auth import get_user_model

from rest_framework import permissions, status, generics
from rest_framework.response import Response
from rest_framework.views import APIView
from django.contrib.auth.models import Permission

from .models import CustomUser, Role, Employee
from .serializers import UserSerializer, RoleSerializer, CreateUserWithRoleSerializer, EmployeeSerializer
from .utils import generate_activation_link
from users.utils import generate_activation_link, send_resend_email

User = get_user_model()

from rest_framework.permissions import BasePermission

class IsSystemAdmin(BasePermission):
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True
        role = getattr(request.user, 'role', None)
        if role and 'admin' in role.name.lower():
            return True
        return False

# ────────────────────────────────────────────────────────────────
# Auth Views
# ────────────────────────────────────────────────────────────────

class SignupView(APIView):
    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({"message": "Signup successful"}, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    def post(self, request):
        email = request.data.get("email")
        password = request.data.get("password")

        try:
            user_obj = CustomUser.objects.get(email=email)
            user = authenticate(request, username=user_obj.username, password=password)
        except CustomUser.DoesNotExist:
            user = None

        if user:
            login(request, user)
            return Response({"message": "Login successful"})
        return Response({"error": "Invalid credentials"}, status=401)



# ────────────────────────────────────────────────────────────────
# User Views
# ────────────────────────────────────────────────────────────────

class UserListCreateView(APIView):
    permission_classes = [IsSystemAdmin]

    def get(self, request):
        users = CustomUser.objects.all()
        serializer = UserSerializer(users, many=True)
        return Response(serializer.data)

    def post(self, request):
        serializer = UserSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save(is_active=False)
            try:
                send_activation_email(user)
            except Exception as e:
                logger.error("Email error: %s", e)

            return Response({
                "message": "User successfully created. Activation email will be sent shortly.",
                "user": serializer.data
            }, status=status.HTTP_201_CREATED)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDetailView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request, id):
        try:
            user = CustomUser.objects.get(id=id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user)
        return Response(serializer.data)


class UserUpdateView(APIView):
    permission_classes = [IsSystemAdmin]

    def put(self, request, id):
        try:
            user = CustomUser.objects.get(id=id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        serializer = UserSerializer(user, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class UserDeleteView(APIView):
    permission_classes = [IsSystemAdmin]

    def delete(self, request, id):
        try:
            user = CustomUser.objects.get(id=id)
        except CustomUser.DoesNotExist:
            return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)
        user.delete()
        return Response({"detail": "User permanently deleted"})


class UserStatsView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        total = CustomUser.objects.count()
        active = CustomUser.objects.filter(is_active=True).count()
        inactive = CustomUser.objects.filter(is_active=False).count()
        employees = Employee.objects.count()
        return Response({
            "total_users": total,
            "active_users": active,
            "inactive_users": inactive,
            "employees": employees
        })


class CurrentUserView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def get(self, request):
        user = request.user
        role_data = None
        if hasattr(user, 'role') and user.role:
            role_data = {
                "id": user.role.id,
                "name": user.role.name,
                "default_route": getattr(user.role, 'default_route', '/dashboard') or '/dashboard'
            }
        return Response({
            "id": user.id,
            "username": user.username,
            "email": user.email,
            "role": role_data if role_data else (getattr(user.role, 'id', None) if getattr(user, 'role', None) else None),
            "is_superuser": user.is_superuser,
            "is_staff": user.is_staff,
            "default_redirect": getattr(user.role, 'default_route', '/dashboard') if hasattr(user, 'role') and user.role else '/dashboard'
        })

# ────────────────────────────────────────────────────────────────
# Role Views
# ────────────────────────────────────────────────────────────────

class RoleListView(generics.ListAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [permissions.IsAuthenticated]

class RoleDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Role.objects.all()
    serializer_class = RoleSerializer
    permission_classes = [IsSystemAdmin]
    lookup_field = 'id'

class EmployeeListCreateView(generics.ListCreateAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]

class EmployeeDetailView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Employee.objects.all()
    serializer_class = EmployeeSerializer
    permission_classes = [permissions.IsAuthenticated]
    lookup_field = 'id'

class AppPermissionsView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    def get(self, request, app_label):
        # Filter out internal/technical and unwanted models that don't need manual permission management
        excluded_models = [
            'emailotp', 'logentry', 'contenttype', 'session', 'role',
            'announcement', 'financerecord', 'incident', 'transaction', 'report'
        ]
        perms = Permission.objects.filter(
            content_type__app_label=app_label
        ).exclude(
            content_type__model__in=excluded_models
        ).exclude(
            codename__icontains='emailotp'
        )
        return Response([{"id": p.id, "name": p.name, "codename": p.codename} for p in perms])


class RoleCreateView(APIView):
    permission_classes = [IsSystemAdmin]

    def post(self, request):
        serializer = RoleSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class CreateUserWithRoleView(APIView):
    """Admin endpoint: create a user and assign their role in one call."""
    permission_classes = [IsSystemAdmin]

    def post(self, request):
        serializer = CreateUserWithRoleSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Deactivate the user so they MUST use the email link to activate
            user.is_active = False
            user.save()

            # Send the activation email
            try:
                send_activation_email(user)
            except Exception as e:
                logger.error("Email error: %s", e)

            return Response({
                "message": "User successfully created. Activation email will be sent shortly.",
                "user": UserSerializer(user).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class AssignRoleView(APIView):
    """Assign or change a user's role."""
    permission_classes = [IsSystemAdmin]

    def put(self, request, id):
        try:
            user = CustomUser.objects.get(pk=id)
        except CustomUser.DoesNotExist:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        role_id = request.data.get('role_id')
        if role_id is None:
            return Response({'detail': 'role_id is required.'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            role = Role.objects.get(pk=role_id)
        except Role.DoesNotExist:
            return Response({'detail': 'Role not found.'}, status=status.HTTP_404_NOT_FOUND)

        user.role = role
        user.save()
        return Response(UserSerializer(user).data)

# ────────────────────────────────────────────────────────────────
# Activation View
# ────────────────────────────────────────────────────────────────

class ActivateUserView(APIView):
    authentication_classes = []
    permission_classes = []

    def get(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({"detail": "Invalid activation link"}, status=400)

        if PasswordResetTokenGenerator().check_token(user, token):
            return Response({"detail": "Token is valid. Please set your password."})
        return Response({"detail": "Invalid or expired token"}, status=400)

    def post(self, request, uidb64, token):
        try:
            uid = urlsafe_base64_decode(uidb64).decode()
            user = CustomUser.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return Response({"detail": "Invalid activation link"}, status=400)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({"detail": "Invalid or expired token"}, status=400)

        password = request.data.get('password')
        if not password:
            return Response({"detail": "Password is required"}, status=400)

        user.set_password(password)
        user.is_active = True
        user.save()
        return Response({"detail": "Account activated successfully. You can now login."})


# ────────────────────────────────────────────────────────────────
# Utility
# ────────────────────────────────────────────────────────────────

def send_activation_email(user):
    activation_link = generate_activation_link(user)
    subject = "Activate your ABV account"
    html = f"""
        <p>Hello {user.username},</p>
        <p>Thanks for signing up! Click the link below to activate your account:</p>
        <p><a href="{activation_link}">Activate Account</a></p>
        <p>If you didn’t request this, you can safely ignore this email.</p>
    """
    send_resend_email(user.email, subject, html)

from .models import Announcement
from .serializers import AnnouncementSerializer

class AnnouncementListCreateView(generics.ListCreateAPIView):
    queryset = Announcement.objects.all().order_by('-created_at')
    serializer_class = AnnouncementSerializer
    permission_classes = [permissions.IsAuthenticated]

    def perform_create(self, serializer):
        if not self.request.user.is_superuser:
            # Maybe check if they have permission to send messages instead?
            # Or just rely on is_superuser for now
            pass
        serializer.save(created_by=self.request.user)

    def post(self, request, *args, **kwargs):
        if not request.user.is_superuser and not getattr(request.user, 'role', None) and not request.user.has_perm('users.add_announcement'):
            # Allow superusers, or you can adjust permissions here
            return Response({'detail': 'You do not have permission to post announcements.'}, status=status.HTTP_403_FORBIDDEN)
        return super().post(request, *args, **kwargs)