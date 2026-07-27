from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
from django.db import models


class Role(models.Model):
    role_name = models.CharField(max_length=50, unique=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "roles"

    def __str__(self):
        return self.role_name


class UserManager(BaseUserManager):
    def create_user(self, email, name, phone=None, password=None, **extra_fields):
        if not email:
            raise ValueError("The email field must be set.")
        if not name:
            raise ValueError("The name field must be set.")

        email = self.normalize_email(email)
        extra_fields.setdefault("is_active", True)
        user = self.model(
            email=email,
            name=name,
            phone=phone,
            **extra_fields,
        )
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, name, phone=None, password=None, **extra_fields):
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        user = self.create_user(email, name, phone=phone, password=password, **extra_fields)
        owner_role, _ = Role.objects.get_or_create(
            role_name="owner",
            defaults={"description": "Full access to entire system"}
        )
        user.roles.add(owner_role)
        return user


class User(AbstractBaseUser, PermissionsMixin):
    name = models.CharField(max_length=150)
    email = models.EmailField(unique=True)
    phone = models.CharField(max_length=20, blank=True, null=True)
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    profileImage = models.ImageField(upload_to="profiles/", null=True, blank=True)
    roles = models.ManyToManyField(
        Role,
        related_name="users",
        blank=True,
        db_table="user_roles",
    )

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["name"]

    def __str__(self):
        return self.email


class Address(models.Model):
    ADDRESS_TYPES = [
        ("HOME", "Home"),
        ("WORK", "Work"),
        ("OTHER", "Other"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="addresses",
    )
    full_name = models.CharField(max_length=150)
    phone_number = models.CharField(max_length=20)
    street_address = models.TextField(help_text="House/Flat No, Street, Landmark, Area")
    city = models.CharField(max_length=100)
    state = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    country = models.CharField(max_length=100, default="India")
    address_type = models.CharField(max_length=10, choices=ADDRESS_TYPES, default="HOME")
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "customer_addresses"
        ordering = ["-is_default", "-created_at"]

    def __str__(self):
        return f"{self.full_name} ({self.address_type}) - {self.city}"

    def save(self, *args, **kwargs):
        if self.is_default:
            # Set all other addresses of this user to is_default=False
            Address.objects.filter(user=self.user).exclude(pk=self.pk).update(is_default=False)
        elif not Address.objects.filter(user=self.user).exclude(pk=self.pk).exists():
            # If this is the user's only address, force it to be default
            self.is_default = True
        super().save(*args, **kwargs)
