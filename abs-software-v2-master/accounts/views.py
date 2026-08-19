from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import CustomTokenObtainPairSerializer
from django.contrib.auth import get_user_model
from users.models import EmailOTP
from users.utils import send_resend_email
import random

User = get_user_model()

class CustomTokenObtainPairView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer

class VerifyOTPView(APIView):
    authentication_classes = [] # Public endpoint since user isn't logged in yet
    permission_classes = []

    def post(self, request):
        user_id = request.data.get('user_id')
        otp_code = request.data.get('otp_code')

        if not user_id or not otp_code:
            return Response({"detail": "User ID and OTP code are required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Find valid OTP
        try:
            otp_record = EmailOTP.objects.filter(user=user, otp_code=otp_code, is_verified=False).latest('created_at')
        except EmailOTP.DoesNotExist:
            return Response({"detail": "Invalid or expired OTP code."}, status=status.HTTP_400_BAD_REQUEST)

        if not otp_record.is_valid():
            return Response({"detail": "Invalid or expired OTP code."}, status=status.HTTP_400_BAD_REQUEST)

        # OTP is valid
        otp_record.is_verified = True
        otp_record.save()

        # Generate standard JWT tokens manually
        refresh = RefreshToken.for_user(user)
        
        # Get role data
        role_data = None
        has_dashboard_access = False
        default_redirect = "/dashboard"
        if user.is_superuser:
            has_dashboard_access = True
            if hasattr(user, 'role') and user.role:
                role_data = {
                    "id": user.role.id,
                    "name": user.role.name,
                    "default_route": getattr(user.role, 'default_route', '/dashboard') or '/dashboard'
                }
                default_redirect = getattr(user.role, 'default_route', None) or "/dashboard"
        elif hasattr(user, 'role') and user.role:
            role_data = {
                "id": user.role.id,
                "name": user.role.name,
                "default_route": getattr(user.role, 'default_route', '/dashboard') or '/dashboard'
            }
            perms = user.role.permissions.all()
            has_dashboard_access = perms.filter(codename='view_dashboardaccess').exists()
            
            # If role has a configured default_route, use it!
            if getattr(user.role, 'default_route', None):
                default_redirect = user.role.default_route
            elif has_dashboard_access:
                default_redirect = "/dashboard"
            else:
                # determine default redirect based on actual module permissions
                codenames = [p.codename for p in perms]
                app_labels = [p.content_type.app_label for p in perms]
                
                has_users_view_permission = any(c in ['view_customuser', 'view_role', 'view_rolemodulepermission'] for c in codenames)
                
                if has_users_view_permission: default_redirect = '/users'
                elif 'equipment' in app_labels: default_redirect = '/equipment'
                elif 'projects' in app_labels: default_redirect = '/project'
                elif 'safety' in app_labels: default_redirect = '/safety'
                elif 'inventory' in app_labels: default_redirect = '/inventory'
                elif 'production' in app_labels: default_redirect = '/production'
                elif 'operations' in app_labels: default_redirect = '/production'
                else: default_redirect = '/unauthorized'

        return Response({
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                "id": user.id,
                "name": getattr(user, "name", user.username),
                "email": user.email,
                "role": role_data,
                "is_superuser": user.is_superuser,
                "mfa_enabled": getattr(user, 'mfa_enabled', False),
                "has_dashboard_access": has_dashboard_access,
                "default_redirect": default_redirect,
            }
        })

class ResendOTPView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        user_id = request.data.get('user_id')

        if not user_id:
            return Response({"detail": "User ID is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"detail": "User not found."}, status=status.HTTP_404_NOT_FOUND)

        # Invalidate previous unverified OTPs
        EmailOTP.objects.filter(user=user, is_verified=False).update(is_verified=True)

        otp_code = str(random.randint(100000, 999999))
        EmailOTP.objects.create(user=user, otp_code=otp_code)
        
        html_content = f"<h2>Your login verification code is: <strong>{otp_code}</strong></h2><p>This code will expire in 10 minutes.</p>"
        send_resend_email(user.email, "Your Login Verification Code", html_content)

from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import PasswordResetTokenGenerator

class PasswordResetRequestView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        email = request.data.get('email')
        if not email:
            return Response({"detail": "Email is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # For security, don't reveal if user exists or not
            return Response({"detail": "If an account with this email exists, a reset link has been sent."})

        # Generate token and uid
        token = PasswordResetTokenGenerator().make_token(user)
        uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
        
        # Link to frontend reset page
        base_url = settings.FRONTEND_URL.rstrip('/')
        reset_link = f"{base_url}/reset-password/{uidb64}/{token}/"
        
        html_content = f"""
        <h2>Password Reset Requested</h2>
        <p>Click the link below to reset your password. This link will expire shortly.</p>
        <a href="{reset_link}" style="padding: 10px 20px; background-color: #2563eb; color: white; text-decoration: none; border-radius: 5px;">Reset Password</a>
        <p>If you did not request this, please ignore this email.</p>
        """
        
        send_resend_email(user.email, "Password Reset Request", html_content)

        return Response({"detail": "If an account with this email exists, a reset link has been sent."})

class PasswordResetConfirmView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request, uidb64, token):
        password = request.data.get('password')
        if not password:
            return Response({"detail": "Password is required."}, status=status.HTTP_400_BAD_REQUEST)

        try:
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            return Response({"detail": "Invalid reset link."}, status=status.HTTP_400_BAD_REQUEST)

        if not PasswordResetTokenGenerator().check_token(user, token):
            return Response({"detail": "Invalid or expired token."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(password)
        user.save()
        return Response({"detail": "Password has been reset successfully. You can now login."})

class ChangePasswordView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        user = request.user
        old_password = request.data.get('old_password')
        new_password = request.data.get('new_password')

        if not old_password or not new_password:
            return Response({"detail": "Both old and new passwords are required."}, status=status.HTTP_400_BAD_REQUEST)

        if not user.check_password(old_password):
            return Response({"detail": "Current password is incorrect."}, status=status.HTTP_400_BAD_REQUEST)

        user.set_password(new_password)
        user.save()
        return Response({"detail": "Password changed successfully."})

