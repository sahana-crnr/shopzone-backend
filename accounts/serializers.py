from dj_rest_auth.registration.serializers import RegisterSerializer as DjRegisterSerializer
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from django.contrib.auth import get_user_model
from .models import Address, Role

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    roles = serializers.SerializerMethodField()
    primary_role = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ("id", "name", "email", "phone", "profileImage", "roles", "primary_role")
        read_only_fields = ("id", "email")

    def get_roles(self, obj):
        return [r.role_name for r in obj.roles.all()]

    def get_primary_role(self, obj):
        user_roles = [r.role_name for r in obj.roles.all()]
        if user_roles:
            return user_roles[0]
        return "admin" if obj.is_staff else "customer"


class AddressSerializer(serializers.ModelSerializer):
    full_address = serializers.SerializerMethodField()

    class Meta:
        model = Address
        fields = (
            "id",
            "full_name",
            "phone_number",
            "street_address",
            "city",
            "state",
            "postal_code",
            "country",
            "address_type",
            "is_default",
            "full_address",
            "created_at",
            "updated_at",
        )
        read_only_fields = ("id", "created_at", "updated_at", "full_address")

    def get_full_address(self, obj):
        parts = [obj.street_address, obj.city, obj.state, obj.postal_code, obj.country]
        return ", ".join([p.strip() for p in parts if p and p.strip()])


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, min_length=6)

    class Meta:
        model = User
        fields = ("name", "email", "phone", "password")

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data["email"],
            name=validated_data["name"],
            phone=validated_data.get("phone", ""),
            password=validated_data["password"],
        )
        customer_role, _ = Role.objects.get_or_create(
            role_name="customer",
            defaults={"description": "Normal user who can browse, order, pay, review, and wishlist products"}
        )
        user.roles.add(customer_role)
        return user


class LoginSerializer(TokenObtainPairSerializer):
    username_field = "email"


class CustomRegisterSerializer(DjRegisterSerializer):
    username = None