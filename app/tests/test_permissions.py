# /mnt/c/Users/Daniel/Documents/webserver/app/tests/test_permissions.py
import os
import tempfile

from django.contrib.auth.models import Permission  # Removed Group F401
from django.test import TestCase
from django.urls import reverse

from ..models import (
    EstadoReporteChoices,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Report,
    Role,
    RoleChoices,
    User,
)


class PermissionTests(TestCase):
    def setUp(self):
        self.admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpassword"
        )
        self.regular_user = User.objects.create_user(
            username="regularuser",
            email="regular@example.com",
            password="regularpassword",
        )
        self.client_role = Role.objects.create(name=RoleChoices.CLIENTE)
        self.gerente_role = Role.objects.create(name=RoleChoices.GERENTE)
        self.director_role = Role.objects.create(name=RoleChoices.DIRECTOR_TECNICO)
        self.tecnico_role = Role.objects.create(name=RoleChoices.PERSONAL_TECNICO_APOYO)
        self.admin_role = Role.objects.create(name=RoleChoices.PERSONAL_ADMINISTRATIVO)

    def test_custom_permissions_exist(self):
        """Test that all custom permissions exist in the system"""
        # Check User model permissions
        self.assertTrue(
            Permission.objects.filter(
                codename="add_external_user",
                content_type__app_label="app",
                content_type__model="user",
            ).exists()
        )

        # Check Equipment model permissions
        self.assertTrue(
            Permission.objects.filter(
                codename="manage_equipment",
                content_type__app_label="app",
                content_type__model="equipment",
            ).exists()
        )

        # Check Report model permissions
        self.assertTrue(
            Permission.objects.filter(
                codename="upload_report",
                content_type__app_label="app",
                content_type__model="report",
            ).exists()
        )

        self.assertTrue(
            Permission.objects.filter(
                codename="approve_report",
                content_type__app_label="app",
                content_type__model="report",
            ).exists()
        )

    def test_add_external_user_permission(self):
        """Test that users with add_external_user permission can create external users only"""
        add_external_user_perm = Permission.objects.get(codename="add_external_user")
        admin_user = User.objects.create_user(
            username="adminstaff", email="adminstaff@example.com", password="password"
        )
        admin_user.roles.add(self.admin_role)
        admin_user.user_permissions.add(add_external_user_perm)
        self.assertTrue(admin_user.has_perm("app.add_external_user"))
        self.client.login(username="adminstaff", password="password")

    def test_manage_equipment_permission(self):
        """Test that users with manage_equipment permission can create and edit equipment"""
        manage_equipment_perm = Permission.objects.get(codename="manage_equipment")
        tech_user = User.objects.create_user(
            username="techstaff", email="tech@example.com", password="password"
        )
        tech_user.roles.add(self.tecnico_role)
        tech_user.user_permissions.add(manage_equipment_perm)
        self.assertTrue(tech_user.has_perm("app.manage_equipment"))

        director_user = User.objects.create_user(
            username="director", email="director@example.com", password="password"
        )
        director_user.roles.add(self.director_role)
        director_user.user_permissions.add(manage_equipment_perm)
        self.assertTrue(director_user.has_perm("app.manage_equipment"))

    def test_report_permissions(self):
        """Test report upload and approval permissions"""
        upload_report_perm = Permission.objects.get(codename="upload_report")
        approve_report_perm = Permission.objects.get(codename="approve_report")

        tech_user = User.objects.create_user(
            username="tech2", email="tech2@example.com", password="password"
        )
        tech_user.roles.add(self.tecnico_role)
        tech_user.user_permissions.add(upload_report_perm)
        self.assertTrue(tech_user.has_perm("app.upload_report"))
        self.assertFalse(tech_user.has_perm("app.approve_report"))

        director_user = User.objects.create_user(
            username="director2", email="director2@example.com", password="password"
        )
        director_user.roles.add(self.director_role)
        director_user.user_permissions.add(upload_report_perm)
        director_user.user_permissions.add(approve_report_perm)
        self.assertTrue(director_user.has_perm("app.upload_report"))
        self.assertTrue(director_user.has_perm("app.approve_report"))

        client_user = User.objects.create_user(
            username="client", email="client@example.com", password="password"
        )
        client_user.roles.add(self.client_role)
        self.assertFalse(client_user.has_perm("app.upload_report"))
        self.assertFalse(client_user.has_perm("app.approve_report"))

    def test_group_based_permissions(self):
        """Test that permissions can be assigned through groups and are correctly inherited by users"""
        from django.contrib.auth.models import Group  # Moved Group import here

        gerente_group = Group.objects.create(
            name="gerente_group_test"
        )  # Changed name to avoid conflict if tests run multiple times without db flush
        manage_equipment_perm = Permission.objects.get(codename="manage_equipment")
        gerente_group.permissions.add(manage_equipment_perm)

        tech_user = User.objects.create_user(
            username="group_tech", email="group_tech@example.com", password="password"
        )
        self.assertFalse(tech_user.has_perm("app.manage_equipment"))

        tech_user.groups.add(gerente_group)
        # It's crucial to refresh the user object from the database or use a new instance
        # to ensure the permission cache is updated after group membership changes.
        tech_user = User.objects.get(pk=tech_user.pk)  # Re-fetch the user

        self.assertTrue(
            tech_user.has_perm("app.manage_equipment"),
            "User should have manage_equipment perm after group add and re-fetch",
        )

        upload_report_perm = Permission.objects.get(codename="upload_report")
        gerente_group.permissions.add(upload_report_perm)

        # Re-fetch or refresh again after modifying group's permissions if user already in group
        tech_user = User.objects.get(pk=tech_user.pk)  # Re-fetch the user

        self.assertTrue(
            tech_user.has_perm("app.upload_report"),
            "User should have upload_report perm after group update and re-fetch",
        )

    def test_view_level_permission_protection(self):
        """Test that report creation requires upload_report permission."""
        staff_user = User.objects.create_user(
            username="viewstaff", email="view@example.com", password="password"
        )
        client_role = Role.objects.get(name=RoleChoices.CLIENTE)
        client_user = User.objects.create_user(
            username="testcliente", password="password"
        )
        client_user.roles.add(client_role)
        process = Process.objects.create(
            user=client_user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        report_upload_url = reverse("report_create")
        upload_report_perm = Permission.objects.get(codename="upload_report")
        self.client.login(username="viewstaff", password="password")

        temp_file_path = ""
        try:
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp_file:
                tmp_file.write(b"test content")
                temp_file_path = tmp_file.name

            initial_report_count = Report.objects.count()
            staff_user.user_permissions.add(upload_report_perm)
            staff_user.refresh_from_db()

            with open(temp_file_path, "rb") as pdf:
                data = {
                    "title": "Test Report With Permission",
                    "description": "Testing permission enforcement",
                    "pdf_file": pdf,
                    "process": process.id,
                    "estado_reporte": EstadoReporteChoices.EN_GENERACION,
                    "user": client_user.id,
                }
                response = self.client.post(report_upload_url, data)

            self.assertEqual(Report.objects.count(), initial_report_count + 1)
            self.assertTrue(
                Report.objects.filter(title="Test Report With Permission").exists()
            )

            staff_user.user_permissions.remove(upload_report_perm)
            staff_user.refresh_from_db()

            with open(temp_file_path, "rb") as pdf:
                data = {
                    "title": "Fail Report Without Perm",
                    "description": "Should be forbidden",
                    "pdf_file": pdf,
                    "process": process.id,
                    "estado_reporte": EstadoReporteChoices.EN_GENERACION,
                    "user": client_user.id,
                }
                response = self.client.post(report_upload_url, data)
            self.assertEqual(response.status_code, 403)
            self.assertFalse(
                Report.objects.filter(title="Fail Report Without Perm").exists()
            )
        finally:
            if temp_file_path and os.path.exists(temp_file_path):
                os.unlink(temp_file_path)

            reports_to_delete = Report.objects.filter(
                title__in=["Test Report With Permission", "Fail Report Without Perm"]
            )
            for report in reports_to_delete:
                if (
                    report.pdf_file
                    and hasattr(report.pdf_file, "path")
                    and os.path.exists(report.pdf_file.path)
                ):
                    os.unlink(report.pdf_file.path)
            reports_to_delete.delete()
