from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from accounts.models import Role

User = get_user_model()


class Command(BaseCommand):
    help = "Assign a role (e.g. delivery_staff, inventory_manager, shop_manager) to a user account."

    def add_arguments(self, parser):
        parser.add_argument("email", type=str, help="Email of the user account")
        parser.add_argument("role_name", type=str, help="Role name to assign (e.g. delivery_staff, inventory_manager)")
        parser.add_argument("--replace", action="store_true", help="Replace existing roles instead of adding")

    def handle(self, *args, **options):
        email = options["email"].strip()
        role_name = options["role_name"].strip().lower()
        replace = options["replace"]

        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            self.stderr.write(self.style.ERROR(f"User with email '{email}' not found."))
            return

        try:
            role = Role.objects.get(role_name__iexact=role_name)
        except Role.DoesNotExist:
            available = ", ".join([r.role_name for r in Role.objects.all()])
            self.stderr.write(
                self.style.ERROR(f"Role '{role_name}' does not exist. Available roles: {available}")
            )
            return

        if replace:
            user.roles.set([role])
            self.stdout.write(self.style.SUCCESS(f"Replaced roles for '{email}' with '{role.role_name}'."))
        else:
            user.roles.add(role)
            self.stdout.write(self.style.SUCCESS(f"Assigned role '{role.role_name}' to user '{email}'."))

        current_roles = ", ".join([r.role_name for r in user.roles.all()])
        self.stdout.write(self.style.SUCCESS(f"Current roles for {email}: [{current_roles}]"))
