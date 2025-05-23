from django.apps import apps as django_apps
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.test import TestCase

from ..apps import ROLES_PERMISSIONS
from ..models import Role, RoleChoices, User

# Suppress noisy logging during tests if not needed for debugging this specific module
# logging.disable(logging.CRITICAL)


class TestUserRoleToGroupSyncSignal(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Create roles based on RoleChoices
        for role_choice_value, role_choice_label in RoleChoices.choices:
            Role.objects.get_or_create(name=role_choice_value)

        # Create corresponding groups (signal should also do this, but good for setup clarity)
        for role_choice_value, role_choice_label in RoleChoices.choices:
            Group.objects.get_or_create(name=role_choice_value)

        cls.user = User.objects.create_user(
            username="signaltestuser", password="password"
        )
        cls.cliente_role = Role.objects.get(name=RoleChoices.CLIENTE)
        cls.gerente_role = Role.objects.get(name=RoleChoices.GERENTE)
        cls.director_role = Role.objects.get(name=RoleChoices.DIRECTOR_TECNICO)

        cls.cliente_group = Group.objects.get(name=RoleChoices.CLIENTE)
        cls.gerente_group = Group.objects.get(name=RoleChoices.GERENTE)
        cls.director_group = Group.objects.get(name=RoleChoices.DIRECTOR_TECNICO)

    def test_add_single_role_adds_user_to_group(self):
        """Test that adding a role to a user adds them to the corresponding group."""
        self.user.roles.add(self.cliente_role)
        self.assertIn(self.cliente_group, self.user.groups.all())

    def test_add_multiple_roles_adds_user_to_multiple_groups(self):
        """Test that adding multiple roles adds the user to all corresponding groups."""
        self.user.roles.add(self.cliente_role, self.gerente_role)
        self.assertIn(self.cliente_group, self.user.groups.all())
        self.assertIn(self.gerente_group, self.user.groups.all())

    def test_remove_single_role_removes_user_from_group(self):
        """Test that removing a role from a user removes them from the corresponding group."""
        self.user.roles.add(self.cliente_role)
        self.user.roles.add(
            self.gerente_role
        )  # Add another to ensure only one is removed from groups

        self.user.roles.remove(self.cliente_role)
        self.assertNotIn(self.cliente_group, self.user.groups.all())
        self.assertIn(
            self.gerente_group, self.user.groups.all()
        )  # Still in the other group

    def test_clear_roles_removes_user_from_all_relevant_groups(self):
        """Test that clearing all roles removes the user from all corresponding groups."""
        self.user.roles.add(self.cliente_role, self.gerente_role)
        self.assertIn(self.cliente_group, self.user.groups.all())
        self.assertIn(self.gerente_group, self.user.groups.all())

        self.user.roles.clear()
        self.assertNotIn(self.cliente_group, self.user.groups.all())
        self.assertNotIn(self.gerente_group, self.user.groups.all())
        self.assertEqual(
            self.user.groups.count(), 0
        )  # Assuming no other groups were assigned

    def test_add_role_creates_group_if_not_exists(self):
        """Test that if a group doesn't exist, adding the role to user creates it."""
        new_role_name = "test_dynamic_role"
        new_group_name = new_role_name  # Signal uses role.name for group name

        # Ensure group does not exist
        Group.objects.filter(name=new_group_name).delete()
        self.assertFalse(Group.objects.filter(name=new_group_name).exists())

        # Create the role
        dynamic_role, _ = Role.objects.get_or_create(name=new_role_name)

        # Add role to user
        self.user.roles.add(dynamic_role)

        # Check group was created and user is in it
        self.assertTrue(Group.objects.filter(name=new_group_name).exists())
        new_group = Group.objects.get(name=new_group_name)
        self.assertIn(new_group, self.user.groups.all())

        # Clean up
        dynamic_role.delete()
        new_group.delete()


class TestAssignRolePermissions(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Ensure all permissions are created by Django's default migrate
        pass

    def get_permission(self, codename, model_name, app_label="app"):
        content_type = ContentType.objects.get(app_label=app_label, model=model_name)
        return Permission.objects.get(codename=codename, content_type=content_type)

    def test_assign_role_permissions_on_app_ready(self):
        """Test that AppConfig.assign_role_permissions correctly creates groups and assigns permissions.

        This test simulates the state after migrations and app loading by manually
        calling the method connected to post_migrate.
        """
        app_config = django_apps.get_app_config("app")

        # Manually call the method that's connected to post_migrate
        # This simulates the state after migrations and app loading
        app_config.assign_role_permissions(sender=app_config)

        for role_name, perms_info in ROLES_PERMISSIONS.items():
            # 1. Check group exists
            self.assertTrue(
                Group.objects.filter(name=role_name).exists(),
                f"Group '{role_name}' was not created.",
            )
            group = Group.objects.get(name=role_name)

            # 2. Check permissions assigned to the group
            expected_perms_set = set()
            for codename, model_lower, app_label_perm in perms_info:
                try:
                    perm = self.get_permission(codename, model_lower, app_label_perm)
                    expected_perms_set.add(perm)
                except ContentType.DoesNotExist:
                    self.fail(
                        f"ContentType for {app_label_perm}.{model_lower} not found for permission '{codename}' in role '{role_name}'."
                    )
                except Permission.DoesNotExist:
                    self.fail(
                        f"Permission '{codename}' on {app_label_perm}.{model_lower} not found for role '{role_name}'."
                    )

            actual_perms_set = set(group.permissions.all())

            self.assertEqual(
                expected_perms_set,
                actual_perms_set,
                f"Permissions mismatch for group '{role_name}'.\n"
                f"Expected: {[p.codename for p in expected_perms_set]}\n"
                f"Got: {[p.codename for p in actual_perms_set]}",
            )

    def test_idempotency_of_assign_role_permissions(self):
        """Test that running assign_role_permissions multiple times doesn't cause issues."""
        app_config = django_apps.get_app_config("app")

        # Call first time
        app_config.assign_role_permissions(sender=app_config)

        # Call second time
        app_config.assign_role_permissions(sender=app_config)

        # Re-verify for a sample role
        role_name_sample = RoleChoices.GERENTE.value
        group_sample = Group.objects.get(name=role_name_sample)

        expected_perms_info_sample = ROLES_PERMISSIONS[role_name_sample]
        expected_perms_set_sample = set()
        for codename, model_lower, app_label_perm in expected_perms_info_sample:
            perm = self.get_permission(codename, model_lower, app_label_perm)
            expected_perms_set_sample.add(perm)

        actual_perms_set_sample = set(group_sample.permissions.all())
        self.assertEqual(
            expected_perms_set_sample,
            actual_perms_set_sample,
            f"Permissions mismatch for group '{role_name_sample}' after second run.",
        )


# To run these tests:
# python manage.py test app.tests.test_app_config
