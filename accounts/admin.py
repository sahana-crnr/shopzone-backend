from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin
from .models import User, Role


@admin.register(Role)
class RoleAdmin(admin.ModelAdmin):
    list_display = ("id", "role_name", "description")
    search_fields = ("role_name", "description")
    ordering = ("id",)


@admin.register(User)
class UserAdmin(BaseUserAdmin):
    list_display = ("id", "email", "name", "phone", "get_roles", "is_staff", "is_active")
    list_filter = ("roles", "is_staff", "is_active")
    search_fields = ("email", "name", "phone")
    ordering = ("id",)
    filter_horizontal = ("roles", "groups", "user_permissions")

    fieldsets = (
        (None, {"fields": ("email", "password")}),
        ("Personal info", {"fields": ("name", "phone", "profileImage")}),
        ("Roles & Permissions", {"fields": ("roles", "is_active", "is_staff", "is_superuser", "groups", "user_permissions")}),
    )

    add_fieldsets = (
        (
            None,
            {
                "classes": ("wide",),
                "fields": ("email", "name", "phone", "password1", "password2"),
            },
        ),
    )

    def get_roles(self, obj):
        return ", ".join([r.role_name for r in obj.roles.all()])
    get_roles.short_description = "Assigned Roles"
