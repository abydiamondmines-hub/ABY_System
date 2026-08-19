from django.contrib import admin
from django.urls import path, include
from django.contrib.auth import views as auth_views

from dashboard.views import DashboardSummary
from rest_framework_simplejwt.views import TokenRefreshView
from accounts.views import (
    CustomTokenObtainPairView, VerifyOTPView, ResendOTPView, 
    PasswordResetRequestView, PasswordResetConfirmView, ChangePasswordView
)

from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

schema_view = get_schema_view(
    openapi.Info(
        title="ABV Management API",
        default_version='v1',
        description="API documentation for ABV Management system",
        contact=openapi.Contact(email="support@abv.com"),
        license=openapi.License(name="MIT License"),
    ),
    public=True,
    permission_classes=[permissions.AllowAny],
)

urlpatterns = [
    path('admin/', admin.site.urls),

    # Swagger / OpenAPI documentation
    path('swagger/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
    path('redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),

    # JWT Authentication Endpoints
    path('api/auth/login/', CustomTokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('api/auth/verify-otp/', VerifyOTPView.as_view(), name='verify_otp'),
    path('api/auth/resend-otp/', ResendOTPView.as_view(), name='resend_otp'),

    # Password Reset Endpoints
    path('api/auth/password-reset-request/', PasswordResetRequestView.as_view(), name='password_reset_request'),
    path('api/auth/password-reset-confirm/<uidb64>/<token>/', PasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('api/auth/change-password/', ChangePasswordView.as_view(), name='change_password'),

    # API routes
    path('api/users/', include('users.urls')),
    path('api/safety/', include('safety.urls')),
    path('api/reports/', include('reports.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/equipment/', include('equipment.urls')),
    path('api/inventory/', include('inventory.urls')),
    path('api/dashboard/', include('dashboard.urls')),
    path('api/categories/', include(('category.urls', 'category'), namespace='category')),
    path('api/production/', include('production.urls')),

    # Dashboard summary
    path('api/summary/', DashboardSummary.as_view()),
]
