from rest_framework.permissions import BasePermission, SAFE_METHODS

def check_user_has_perm(user, perm_codename, app_label=None):
    """Check if a user has a specific permission via superuser or role assignment."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, 'role', None)
    if role:
        if 'admin' in role.name.lower():
            return True
        qs = role.permissions.all()
        if app_label:
            qs = qs.filter(content_type__app_label=app_label)
        return qs.filter(codename=perm_codename).exists()
    return False

def check_user_has_app_permission(user, app_label):
    """Check if a user has any permission for a given app module."""
    if not user or not user.is_authenticated:
        return False
    if user.is_superuser:
        return True
    role = getattr(user, 'role', None)
    if role:
        if 'admin' in role.name.lower():
            return True
        return role.permissions.filter(content_type__app_label=app_label).exists()
    return False

class IsSystemAdmin(BasePermission):
    """Allows full access to superusers, staff, or roles with 'admin' in the name."""
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True
        role = getattr(request.user, 'role', None)
        if role and 'admin' in role.name.lower():
            return True
        return False

class HasDashboardAccess(BasePermission):
    """
    Allows access to dashboard endpoints for superusers, staff, admins,
    or users whose role has the 'view_dashboardaccess' permission.
    """
    def has_permission(self, request, view):
        if not request.user or not request.user.is_authenticated:
            return False
        if request.user.is_superuser or getattr(request.user, 'is_staff', False):
            return True
        # Check standard Django user perms or custom role perms
        if request.user.has_perm('users.view_dashboardaccess'):
            return True
        return check_user_has_perm(request.user, 'view_dashboardaccess', 'users')

class HasModulePermission(BasePermission):
    """
    Fine-grained permission class checking role permissions for specific modules/models.
    - SAFE_METHODS (GET, HEAD, OPTIONS): checks 'view_<model>' or module access
    - POST: checks 'add_<model>'
    - PUT, PATCH: checks 'change_<model>'
    - DELETE: checks 'delete_<model>'
    """
    def has_permission(self, request, view):
        user = request.user
        if not user or not user.is_authenticated:
            return False
        if user.is_superuser:
            return True
        role = getattr(user, 'role', None)
        if role and 'admin' in role.name.lower():
            return True
        if not role:
            return False

        app_label = getattr(view, 'required_app', None)
        model_cls = getattr(getattr(view, 'queryset', None), 'model', None)

        if model_cls:
            app_label = app_label or model_cls._meta.app_label
            model_name = model_cls._meta.model_name

            if request.method in SAFE_METHODS:
                action = 'view'
            elif request.method == 'POST':
                action = 'add'
            elif request.method in ['PUT', 'PATCH']:
                action = 'change'
            elif request.method == 'DELETE':
                action = 'delete'
            else:
                action = 'view'

            codename = f"{action}_{model_name}"

            # Check specific model action permission
            if role.permissions.filter(content_type__app_label=app_label, codename=codename).exists():
                return True

            # If viewing (GET/HEAD) and user has any permission in this app module, grant view access
            if request.method in SAFE_METHODS and role.permissions.filter(content_type__app_label=app_label).exists():
                return True

        elif app_label:
            return role.permissions.filter(content_type__app_label=app_label).exists()

        return False
