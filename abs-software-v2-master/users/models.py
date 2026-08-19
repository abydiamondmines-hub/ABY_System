from django.contrib.auth.models import AbstractUser, Permission
from django.db import models

class Role(models.Model):
    name = models.CharField(max_length=100, unique=True)
    description = models.TextField(blank=True, null=True)
    permissions = models.ManyToManyField(Permission, blank=True)
    default_route = models.CharField(max_length=100, default='/dashboard', blank=True, null=True)

    def __str__(self):
        return self.name

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    role = models.ForeignKey(Role, on_delete=models.SET_NULL, null=True, blank=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    mfa_enabled = models.BooleanField(default=False)
    
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']  # Keep username required if needed

    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.email})"

class DashboardAccess(models.Model):
    """
    Proxy model used solely to create a 'view_dashboardaccess' permission
    that controls who can see the main Admin Dashboard.
    """
    class Meta:
        managed = False  # No DB table created
        default_permissions = ()  # No automatic add/change/delete
        permissions = [
            ("view_dashboardaccess", "Can view Admin Dashboard"),
        ]

class RoleModulePermission(models.Model):
    """
    Proxy model to generate permissions for viewing/editing the Permissions tab.
    """
    class Meta:
        managed = False
        default_permissions = ()
        permissions = [
            ("view_rolemodulepermission", "Can view Permissions Tab"),
            ("change_rolemodulepermission", "Can edit Permissions"),
        ]

class Employee(models.Model):
    name = models.CharField(max_length=255)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    rank = models.CharField(max_length=50, choices=[('Administrator', 'Administrator'), ('Manager', 'Manager'), ('Staff', 'Staff')], default='Staff')
    amount = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.name

class EmailOTP(models.Model):
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE)
    otp_code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_verified = models.BooleanField(default=False)

    def is_valid(self):
        # Code is valid for 10 minutes
        from django.utils import timezone
        import datetime
        return not self.is_verified and self.created_at >= timezone.now() - datetime.timedelta(minutes=10)

    def __str__(self):
        return f"OTP for {self.user.email} at {self.created_at}"

class Announcement(models.Model):
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='announcements')

    def __str__(self):
        return f"Announcement by {self.created_by.username if self.created_by else 'Unknown'} at {self.created_at}"
