from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.models import Permission
from .models import Role, CustomUser, Employee

User = get_user_model()

class EmployeeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Employee
        fields = '__all__'

class RoleSerializer(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=Permission.objects.all(),
        required=False
    )

    class Meta:
        model = Role
        fields = ['id', 'name', 'description', 'default_route', 'permissions']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        # Detailed permission info for the frontend
        representation['permissions'] = [
            {"id": p.id, "name": p.name, "codename": p.codename}
            for p in instance.permissions.all()
        ]
        return representation

class UserSerializer(serializers.ModelSerializer):
    role = RoleSerializer(read_only=True)
    role_id = serializers.PrimaryKeyRelatedField(
        queryset=Role.objects.all(),
        source='role',
        write_only=True,
        required=False,
        allow_null=True
    )

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'phone_number', 'role', 'role_id', 'department', 'is_active', 'created_at']
        read_only_fields = ['id', 'created_at']

    def validate_email(self, value):
        qs = CustomUser.objects.filter(email=value)
        if self.instance:
            qs = qs.exclude(pk=self.instance.pk)
        if qs.exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        role = validated_data.pop('role', None)
        is_active = validated_data.pop('is_active', True) # Default to True if not provided
        user = CustomUser(**validated_data)
        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()
        user.is_active = is_active
        if role:
            user.role = role
        user.save()
        return user


class CreateUserWithRoleSerializer(serializers.Serializer):
    """Flat serializer for admin user creation via Roles panel."""
    username = serializers.CharField()
    email = serializers.EmailField()
    phone_number = serializers.CharField(required=False, allow_blank=True)
    department = serializers.CharField(required=False, allow_blank=True)
    password = serializers.CharField(write_only=True)
    role_id = serializers.IntegerField()

    def validate_email(self, value):
        if CustomUser.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate_username(self, value):
        if CustomUser.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with this name already exists.")
        return value

    def validate_role_id(self, value):
        try:
            return Role.objects.get(pk=value)
        except Role.DoesNotExist:
            raise serializers.ValidationError("Role not found.")

    def create(self, validated_data):
        role = validated_data.pop('role_id')  # already resolved to Role instance
        password = validated_data.pop('password')
        user = CustomUser(**validated_data)
        user.set_password(password)
        user.is_active = True
        user.role = role
        user.save()
        return user

from .models import Announcement

class AnnouncementSerializer(serializers.ModelSerializer):
    created_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Announcement
        fields = ['id', 'message', 'created_at', 'created_by_name']

    def get_created_by_name(self, obj):
        return obj.created_by.username if obj.created_by else "Admin"

