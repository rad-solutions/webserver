import os
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from .models import Report, User


class UserModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

    def test_user_creation(self):
        """Test que la creación de un usuario funciona correctamente"""
        self.assertEqual(self.user.username, "testuser")
        self.assertEqual(self.user.email, "test@example.com")
        self.assertEqual(self.user.first_name, "Test")
        self.assertEqual(self.user.last_name, "User")
        self.assertTrue(self.user.check_password("testpassword"))
        self.assertTrue(self.user.created_at is not None)

    def test_user_string_representation(self):
        """Test que la representación de cadena del usuario es correcta"""
        expected_string = "Test User (test@example.com)"
        self.assertEqual(str(self.user), expected_string)


class ReportModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser",
            email="test@example.com",
            password="testpassword",
            first_name="Test",
            last_name="User",
        )

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"contenido de prueba del PDF")
        self.temp_file.close()

        with open(self.temp_file.name, "rb") as pdf:
            self.report = Report.objects.create(
                user=self.user,
                title="Informe de prueba",
                description="Esta es una descripción de prueba",
                pdf_file=SimpleUploadedFile("test.pdf", pdf.read()),
            )

    def tearDown(self):
        os.unlink(self.temp_file.name)
        if os.path.exists(self.report.pdf_file.path):
            os.unlink(self.report.pdf_file.path)

    def test_report_creation(self):
        """Test que la creación de un informe funciona correctamente"""
        self.assertEqual(self.report.user, self.user)
        self.assertEqual(self.report.title, "Informe de prueba")
        self.assertEqual(self.report.description, "Esta es una descripción de prueba")
        self.assertTrue(self.report.pdf_file)
        self.assertTrue(self.report.created_at is not None)

    def test_report_string_representation(self):
        expected_string = "Report by Test: Informe de prueba"
        self.assertEqual(str(self.report), expected_string)

    def test_user_reports_relationship(self):
        self.assertEqual(self.user.reports.count(), 1)
        self.assertEqual(self.user.reports.first(), self.report)


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

        self.client.login(username="testuser", password="testpassword")

    def tearDown(self):
        os.unlink(self.temp_file.name)

        for report in Report.objects.all():
            if os.path.exists(report.pdf_file.path):
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
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 302)
            self.assertEqual(Report.objects.count(), 1)
        self.assertTrue(True)

    def test_report_creation_no_file(self):
        url = reverse("report_create")
        data = {
            "title": "Informe sin archivo",
            "description": "Este informe no tiene archivo PDF",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Report.objects.count(), 0)

    def test_report_creation_no_title(self):
        url = reverse("report_create")
        with open(self.temp_file.name, "rb") as pdf:
            data = {
                "description": "Este informe no tiene título",
                "pdf_file": pdf,
            }
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 200)
            self.assertEqual(Report.objects.count(), 0)

    def test_report_update_view(self):

        with open(self.temp_file.name, "rb") as pdf:
            report = Report.objects.create(
                user=self.user,
                title="Informe para actualizar",
                description="Descripción original",
                pdf_file=SimpleUploadedFile("test.pdf", pdf.read()),
            )

        url = reverse("report_update", args=[report.id])
        data = {
            "title": "Título actualizado",
            "description": "Descripción actualizada",
        }
        response = self.client.post(url, data)

        self.assertEqual(response.status_code, 302)

        report.refresh_from_db()
        self.assertEqual(report.title, "Título actualizado")
        self.assertEqual(report.description, "Descripción actualizada")

        with open(self.temp_file.name, "rb") as pdf:
            data["pdf_file"] = pdf
            response = self.client.post(url, data)
            self.assertEqual(response.status_code, 302)

    def test_report_delete_view(self):
        with open(self.temp_file.name, "rb") as pdf:
            report = Report.objects.create(
                user=self.user,
                title="Informe para eliminar",
                description="Este informe será eliminado",
                pdf_file=SimpleUploadedFile("test.pdf", pdf.read()),
            )

        url = reverse("report_delete", args=[report.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
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
        self.assertEqual(response.status_code, 302)

    def test_login_invalid_username(self):
        url = reverse("login")
        data = {
            "username": "nonexistentuser",
            "password": "testpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_login_invalid_password(self):
        url = reverse("login")
        data = {
            "username": "testuser",
            "password": "wrongpassword",
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)  # Vuelve al formulario
        self.assertFalse(response.wsgi_request.user.is_authenticated)

    def test_logout(self):
        self.client.login(username="testuser", password="testpassword")
        self.assertTrue(self.client.session.get("_auth_user_id"))

        url = reverse("logout")
        response = self.client.get(url)
        self.assertEqual(
            response.status_code, 302
        )  # Redirección después de cerrar sesión
        self.assertFalse(self.client.session.get("_auth_user_id"))


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

        with open(self.temp_file.name, "rb") as pdf:
            self.report = Report.objects.create(
                user=self.user,
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
