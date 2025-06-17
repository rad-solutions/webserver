import os
import tempfile

from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase
from django.urls import reverse

from ..models import (
    Equipment,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
    Report,
    User,
)


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

        self.process_for_urls = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.equipment_for_urls = Equipment.objects.create(
            nombre="Equipo Test URL", user=self.user, process=self.process_for_urls
        )
        # Crear un archivo temporal para el reporte
        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"dummy content")
        self.temp_file.seek(0)
        self.report_for_urls = Report.objects.create(
            user=self.user,
            process=self.process_for_urls,
            title="Reporte Test URL",
            pdf_file=SimpleUploadedFile("url_test.pdf", self.temp_file.read()),
        )

    def tearDown(self):
        self.temp_file.close()
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)
        if self.report_for_urls.pdf_file and hasattr(
            self.report_for_urls.pdf_file, "path"
        ):
            if os.path.exists(self.report_for_urls.pdf_file.path):
                try:
                    os.remove(self.report_for_urls.pdf_file.path)
                except OSError:
                    pass

    def test_unauthenticated_access(self):
        """Test que los usuarios no autenticados son redirigidos al inicio de sesión"""
        urls_to_test = {
            "report_list": reverse("report_list"),
            "report_create": reverse("report_create"),
            "report_detail": reverse("report_detail", args=[self.report_for_urls.id]),
            "report_update": reverse("report_update", args=[self.report_for_urls.id]),
            "report_delete": reverse("report_delete", args=[self.report_for_urls.id]),
            "equipos_list": reverse("equipos_list"),
            "equipos_create": reverse("equipos_create"),
            "equipos_detail": reverse(
                "equipos_detail", args=[self.equipment_for_urls.id]
            ),
            "equipos_update": reverse(
                "equipos_update", args=[self.equipment_for_urls.id]
            ),
            "equipos_delete": reverse(
                "equipos_delete", args=[self.equipment_for_urls.id]
            ),
            "process_list": reverse("process_list"),
            "process_create": reverse("process_create"),
            "process_detail": reverse(
                "process_detail", args=[self.process_for_urls.id]
            ),
            "process_update": reverse(
                "process_update", args=[self.process_for_urls.id]
            ),
            "process_delete": reverse(
                "process_delete", args=[self.process_for_urls.id]
            ),
            "user_list": reverse("user_list"),
            "user_create": reverse("user_create"),
            # Añadir user_detail, user_update, user_delete si es necesario
        }

        for name, url in urls_to_test.items():
            with self.subTest(url_name=name):
                response = self.client.get(url)
                self.assertEqual(response.status_code, 302, f"Failed for GET {url}")
                self.assertTrue(
                    response.url.startswith("/login/"), f"Failed for GET {url}"
                )

                # Para vistas create, update, delete, también probar POST si es relevante
                # (aunque DeleteView y UpdateView suelen requerir GET primero para la confirmación/formulario)
                if "create" in name or "update" in name or "delete" in name:
                    response_post = self.client.post(url, {})
                    self.assertEqual(
                        response_post.status_code, 302, f"Failed for POST {url}"
                    )
                    self.assertTrue(
                        response_post.url.startswith("/login/"),
                        f"Failed for POST {url}",
                    )
