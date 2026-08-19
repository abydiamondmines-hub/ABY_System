from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth import authenticate, get_user_model

User = get_user_model()

class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        email = attrs.get("email")
        password = attrs.get("password")

        try:
            user_obj = User.objects.get(email=email)
        except User.DoesNotExist:
            raise serializers.ValidationError("Invalid credentials")

        user = authenticate(email=email, password=password)

        if not user or not user.is_active:
            raise serializers.ValidationError("Invalid credentials")

        if getattr(user, 'mfa_enabled', False):
            import random
            from users.models import EmailOTP
            from users.utils import send_resend_email
            
            # Generate 6-digit OTP
            otp_code = str(random.randint(100000, 999999))
            EmailOTP.objects.create(user=user, otp_code=otp_code)
            
            # Send Email
            html_content = f"<h2>Your login verification code is: <strong>{otp_code}</strong></h2><p>This code will expire in 10 minutes.</p>"
            send_resend_email(user.email, "Your Login Verification Code", html_content)
            
            return {
                "mfa_required": True,
                "user_id": user.id,
                "email": user.email,
                "message": "Verification code sent to your email."
            }

        # Pass email and password to super().validate()
        data = super().validate({
            "email": email,
            "password": password
        })

        # Get the role object if the user has a role
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

        data["user"] = {
            "id": user.id,
            "name": getattr(user, "name", user.username),
            "email": user.email,
            "role": role_data,
            "is_superuser": user.is_superuser,
            "mfa_enabled": getattr(user, 'mfa_enabled', False),
            "has_dashboard_access": has_dashboard_access,
            "default_redirect": default_redirect,
        }

        return data
