from django.contrib.auth import get_user_model
from django.test import TestCase

from app.apps import ROLES_PERMISSIONS
from app.models import RoleChoices
from app.scripts.create_users import run as create_users_script

User = get_user_model()


class UserRolePermissionIntegrationTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        # Run the script to create users and assign roles/groups
        # This assumes that migrations (including group creation and permission assignment)
        # have already run as part of the test setup.
        create_users_script()

    def _check_permissions(self, username, role_key_value):
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist:
            self.fail(f"User {username} was not created by the script.")

        # Get expected permissions for this role from ROLES_PERMISSIONS
        # ROLES_PERMISSIONS maps role names (e.g., "cliente") to lists of permission tuples
        expected_perms_tuples = ROLES_PERMISSIONS.get(role_key_value, [])
        expected_perms_strings = {
            f"{app_label}.{codename}"
            for codename, model_lower, app_label in expected_perms_tuples
        }

        # Get all permissions defined across all roles in ROLES_PERMISSIONS
        # These are the permissions we are explicitly managing through roles.
        all_managed_perms_in_config = set()
        for r_key, perms_list in ROLES_PERMISSIONS.items():
            for codename, model_lower, app_label in perms_list:
                all_managed_perms_in_config.add(f"{app_label}.{codename}")

        # Check if user has all expected permissions
        for perm_string in expected_perms_strings:
            self.assertTrue(
                user.has_perm(perm_string),
                f"User {username} (role: {role_key_value}) should have permission '{perm_string}'.",
            )

        # Check user does NOT have managed permissions they shouldn't have
        # (i.e., permissions defined for other roles in ROLES_PERMISSIONS but not this one)
        for perm_string in all_managed_perms_in_config:
            if perm_string not in expected_perms_strings:
                self.assertFalse(
                    user.has_perm(perm_string),
                    f"User {username} (role: {role_key_value}) should NOT have permission '{perm_string}'.",
                )

    def test_cliente_permissions(self):
        self._check_permissions("cliente_test", RoleChoices.CLIENTE.value)

    def test_gerente_permissions(self):
        self._check_permissions("gerente_test", RoleChoices.GERENTE.value)

    def test_director_tecnico_permissions(self):
        self._check_permissions("director_test", RoleChoices.DIRECTOR_TECNICO.value)

    def test_personal_tecnico_apoyo_permissions(self):
        self._check_permissions(
            "tecnico_apoyo_test", RoleChoices.PERSONAL_TECNICO_APOYO.value
        )

    def test_personal_administrativo_permissions(self):
        # The username for this role in create_users.py is "admin_staff_test"
        self._check_permissions(
            "admin_staff_test", RoleChoices.PERSONAL_ADMINISTRATIVO.value
        )

    def test_admin_user_is_superuser(self):
        try:
            admin_user = User.objects.get(username="admin")
        except User.DoesNotExist:
            self.fail("Default admin user 'admin' was not created by the script.")

        self.assertTrue(admin_user.is_superuser, "User 'admin' should be a superuser.")
        self.assertTrue(admin_user.is_staff, "User 'admin' should be staff.")

        # Superusers implicitly have all permissions.
        # We can check a few critical ones as a sanity check.
        # These permissions might or might not be in ROLES_PERMISSIONS but a superuser has them.
        self.assertTrue(
            admin_user.has_perm("app.add_report"), "Admin should have 'app.add_report'."
        )
        self.assertTrue(
            admin_user.has_perm("app.change_user"),
            "Admin should have 'app.change_user'.",
        )
        self.assertTrue(
            admin_user.has_perm("app.delete_equipment"),
            "Admin should have 'app.delete_equipment'.",
        )
