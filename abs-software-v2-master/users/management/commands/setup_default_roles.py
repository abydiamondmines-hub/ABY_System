from django.core.management.base import BaseCommand
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from users.models import Role

class Command(BaseCommand):
    help = "Initializes default strict roles and attaches their corresponding permissions."

    def handle(self, *args, **options):
        self.stdout.write("Configuring default strict roles...")

        role_configs = [
            {
                "name": "Administrator",
                "description": "Full access to all system modules, user administration, and settings.",
                "default_route": "/dashboard",
                "apps": ["all"]
            },
            {
                "name": "Equipment Manager",
                "description": "Manage equipment inventory, status, maintenance, and allocation.",
                "default_route": "/equipment",
                "apps": ["equipment"]
            },
            {
                "name": "Project Manager",
                "description": "Oversee projects, site tasks, and milestone progress.",
                "default_route": "/project",
                "apps": ["projects"]
            },
            {
                "name": "Safety Officer",
                "description": "Handle risk assessments, safety logs, and incident reporting.",
                "default_route": "/safety",
                "apps": ["safety"]
            },
            {
                "name": "Inventory Manager",
                "description": "Control warehouse items, stock levels, and supply restocking.",
                "default_route": "/inventory",
                "apps": ["inventory"]
            },
            {
                "name": "Production Manager",
                "description": "Manage daily extraction, operations logs, and machinery maintenance.",
                "default_route": "/production",
                "apps": ["operations", "production"]
            },
        ]

        # Ensure all content types and permissions are accessible
        for config in role_configs:
            role, created = Role.objects.get_or_create(name=config["name"])
            role.description = config["description"]
            role.default_route = config["default_route"]
            role.save()

            if "all" in config["apps"]:
                # Admin gets all permissions
                all_perms = Permission.objects.all()
                role.permissions.set(all_perms)
            else:
                # Filter permissions by specified apps
                app_perms = Permission.objects.filter(content_type__app_label__in=config["apps"])
                role.permissions.set(app_perms)

            action = "Created" if created else "Updated"
            self.stdout.write(self.style.SUCCESS(
                f"✓ {action} role: '{role.name}' -> Default Route: '{role.default_route}' ({role.permissions.count()} permissions)"
            ))

        # Automatically assign Administrator role to existing superusers without a role
        try:
            admin_role = Role.objects.get(name="Administrator")
            from users.models import CustomUser
            for user in CustomUser.objects.filter(is_superuser=True, role__isnull=True):
                user.role = admin_role
                user.save()
                self.stdout.write(self.style.SUCCESS(f"✓ Assigned Administrator role to superuser: {user.email}"))
        except Exception as e:
            self.stdout.write(self.style.WARNING(f"Superuser role assignment note: {e}"))

        self.stdout.write(self.style.SUCCESS("All default strict roles successfully initialized!"))
