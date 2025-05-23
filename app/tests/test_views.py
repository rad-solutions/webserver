import os
import tempfile

from django.contrib.auth.models import Permission
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ..models import (
    EstadoReporteChoices,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Report,
    User,
)


class ReportAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpassword",
            first_name="Admin",
            last_name="User",
            is_staff=True,
            is_superuser=True,
        )

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"contenido de prueba del PDF")
        self.temp_file.close()

        # ProcessType and ProcessStatus are now CharFields, no need to create them as objects
        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,  # Use choice directly
            estado=ProcessStatusChoices.EN_PROGRESO,  # Use choice directly
        )

        self.client.login(username="testuser", password="testpassword")

        # Add all necessary permissions for ReportAPITest user
        view_report_perm = Permission.objects.get(codename="view_report")
        add_report_perm = Permission.objects.get(
            codename="add_report"
        )  # Though upload_report is used in ReportCreateView
        upload_report_perm = Permission.objects.get(codename="upload_report")
        change_report_perm = Permission.objects.get(codename="change_report")
        delete_report_perm = Permission.objects.get(codename="delete_report")

        self.user.user_permissions.add(
            view_report_perm,
            add_report_perm,  # Adding for completeness, view uses upload_report
            upload_report_perm,
            change_report_perm,
            delete_report_perm,
        )

    def tearDown(self):
        os.unlink(self.temp_file.name)

        for report in Report.objects.all():
            if report.pdf_file and os.path.exists(
                report.pdf_file.path
            ):  # Check if pdf_file exists
                os.unlink(report.pdf_file.path)

    def test_report_list_view(self):
        url = reverse("report_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)

    def test_report_creation_view(self):
        url = reverse("report_create")
        with open(self.temp_file.name, "rb") as pdf:
            data = {
                "title": "Nuevo informe de prueba",
                "description": "Descripción del nuevo informe",
                "pdf_file": pdf,
                "process": self.process.id,
                "estado_reporte": EstadoReporteChoices.EN_GENERACION,
            }
            response = self.client.post(url, data)
            self.assertEqual(
                response.status_code, 302
            )  # Should redirect after successful creation
            self.assertEqual(Report.objects.count(), 1)
            # self.assertTrue(True) # This assertion is redundant

    def test_report_creation_no_file(self):
        url = reverse("report_create")
        data = {
            "title": "Informe sin archivo",
            "description": "Este informe no tiene archivo PDF",
            "process": self.process.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Should re-render form with errors
        self.assertEqual(Report.objects.count(), 0)

    def test_report_creation_no_title(self):
        url = reverse("report_create")
        with open(self.temp_file.name, "rb") as pdf:
            data = {
                "description": "Este informe no tiene título",
                "pdf_file": pdf,
                "process": self.process.id,
            }
            response = self.client.post(url, data)
            self.assertEqual(
                response.status_code, 200
            )  # Should re-render form with errors
            self.assertEqual(Report.objects.count(), 0)

    def test_report_update_view(self):
        with open(self.temp_file.name, "rb") as pdf:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe para actualizar",
                description="Descripción original",
                pdf_file=SimpleUploadedFile("test.pdf", pdf.read()),
            )

        url = reverse("report_update", args=[report.id])
        data = {
            "title": "Título actualizado",
            "description": "Descripción actualizada",
            "process": self.process.id,
            "estado_reporte": EstadoReporteChoices.REVISADO,
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.title, "Título actualizado")
        self.assertEqual(report.description, "Descripción actualizada")
        self.assertEqual(report.estado_reporte, EstadoReporteChoices.REVISADO)

        # Test updating with a new file (optional, but good to have)
        with open(self.temp_file.name, "rb") as pdf:  # Re-open for the new upload
            data["pdf_file"] = pdf
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 302)  # Should redirect

    def test_report_delete_view(self):
        with open(self.temp_file.name, "rb") as pdf:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe para eliminar",
                description="Este informe será eliminado",
                pdf_file=SimpleUploadedFile("test.pdf", pdf.read()),
            )

        url = reverse("report_delete", args=[report.id])
        response = self.client.post(url)  # POST for delete confirm usually
        self.assertEqual(response.status_code, 302)  # Redirect after delete
        self.assertEqual(Report.objects.count(), 0)


class AuthenticationTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

    def test_login_successful(self):
        url = reverse("login")
        data = {
            "username": "testuser",
            "password": "testpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)  # Successful login redirects
        self.assertTrue(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_username(self):
        url = reverse("login")
        data = {
            "username": "nonexistentuser",
            "password": "testpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders login form
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_password(self):
        url = reverse("login")
        data = {
            "username": "testuser",
            "password": "wrongpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Re-renders login form
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        self.client.login(username="testuser", password="testpassword")
        self.assertTrue(self.client.session.get("_auth_user_id") is not None)

        url = reverse("logout")
        response = self.client.get(url)  # Logout is usually a GET request
        self.assertEqual(response.status_code, 302)  # Redirects after logout
        self.assertIsNone(self.client.session.get("_auth_user_id"))


class ProtectedResourceTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

        self.other_user = User.objects.create_user(
            username="otheruser",
            email="other@example.com",
            password="otherpassword",
            first_name="Other",
            last_name="User",
        )

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"contenido de prueba del PDF")
        self.temp_file.close()

        # Create process and report needed for test_unauthenticated_access
        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        with open(self.temp_file.name, "rb") as pdf:
            self.report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe del primer usuario",
                description="Este informe pertenece al primer usuario",
                pdf_file=SimpleUploadedFile("test.pdf", pdf.read()),
            )

    def tearDown(self):
        os.unlink(self.temp_file.name)

        for report in Report.objects.all():
            if os.path.exists(report.pdf_file.path):
                os.unlink(report.pdf_file.path)

    def test_unauthenticated_access(self):
        """Test que los usuarios no autenticados son redirigidos al inicio de sesión"""
        url = reverse("report_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

        url = reverse("report_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))

        url = reverse("report_detail", args=[self.report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 302)
        self.assertTrue(response.url.startswith("/login/"))
