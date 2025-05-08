import os
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import (
    Equipment,
    Process,
    ProcessStatus,
    ProcessStatusChoices,
    ProcessType,
    ProcessTypeChoices,
    Report,
    Role,
    RoleChoices,
    User,
)


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

    def test_username_required(self):
        """Username cannot be blank."""
        with self.assertRaises(ValueError):
            User.objects.create_user(
                username="", email="foo@example.com", password="pwd"
            )

    def test_duplicate_username(self):
        """Creating two users with the same username should fail."""
        User.objects.create_user(
            username="dupuser", email="first@example.com", password="pwd"
        )
        with self.assertRaises(IntegrityError):
            User.objects.create_user(
                username="dupuser", email="second@example.com", password="pwd"
            )


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

    def test_missing_title_validation(self):
        """Cannot create report without title."""
        rpt = Report(
            user=self.user,
            description="No title provided",
            pdf_file=SimpleUploadedFile("no_title.pdf", b"data"),
        )
        with self.assertRaises(ValidationError):
            rpt.full_clean()

    def test_missing_pdf_validation(self):
        """Cannot create report without PDF file."""
        rpt = Report(
            user=self.user,
            title="Has Title",
            description="But no file",
        )
        with self.assertRaises(ValidationError):
            rpt.full_clean()


class RoleModelTest(TestCase):
    def test_role_creation(self):
        """Test that role creation works correctly."""
        role = Role.objects.create(name=RoleChoices.CLIENTE)
        self.assertEqual(role.name, "cliente")
        self.assertEqual(Role.objects.count(), 1)

    def test_role_string_representation(self):
        """Test the string representation of the role."""
        role = Role.objects.create(name=RoleChoices.EMPLEADO)
        self.assertEqual(str(role), "Empleado")

    def test_role_uniqueness(self):
        """Test that role names must be unique."""
        Role.objects.create(name=RoleChoices.CLIENTE)
        with self.assertRaises(IntegrityError):
            Role.objects.create(name=RoleChoices.CLIENTE)


class ProcessTypeModelTest(TestCase):
    def test_process_type_creation(self):
        """Test process type creation."""
        pt = ProcessType.objects.create(process_type=ProcessTypeChoices.ASESORIA)
        self.assertEqual(pt.process_type, "asesoria")
        self.assertEqual(ProcessType.objects.count(), 1)

    def test_process_type_string_representation(self):
        """Test the string representation."""
        pt = ProcessType.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES
        )
        self.assertEqual(str(pt), "Cálculo de Blindajes")

    def test_process_type_uniqueness(self):
        """Test process type uniqueness."""
        ProcessType.objects.create(process_type=ProcessTypeChoices.CONTROL_CALIDAD)
        with self.assertRaises(IntegrityError):
            ProcessType.objects.create(process_type=ProcessTypeChoices.CONTROL_CALIDAD)


class ProcessStatusModelTest(TestCase):
    def test_process_status_creation(self):
        """Test process status creation."""
        ps = ProcessStatus.objects.create(estado=ProcessStatusChoices.EN_PROGRESO)
        self.assertEqual(ps.estado, "en_progreso")
        self.assertEqual(ProcessStatus.objects.count(), 1)

    def test_process_status_string_representation(self):
        """Test the string representation."""
        ps = ProcessStatus.objects.create(estado=ProcessStatusChoices.FINALIZADO)
        self.assertEqual(str(ps), "Finalizado")

    def test_process_status_uniqueness(self):
        """Test process status uniqueness."""
        ProcessStatus.objects.create(estado=ProcessStatusChoices.RADICADO)
        with self.assertRaises(IntegrityError):
            ProcessStatus.objects.create(estado=ProcessStatusChoices.RADICADO)


class ProcessModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="procuser", password="password")
        self.process_type = ProcessType.objects.create(
            process_type=ProcessTypeChoices.ASESORIA
        )
        self.process_status = ProcessStatus.objects.create(
            estado=ProcessStatusChoices.EN_PROGRESO
        )

    def test_process_creation(self):
        """Test process creation and relationships."""
        process = Process.objects.create(
            user=self.user,
            process_type=self.process_type,
            estado=self.process_status,
        )
        self.assertEqual(process.user, self.user)
        self.assertEqual(process.process_type, self.process_type)
        self.assertEqual(process.estado, self.process_status)
        self.assertIsNotNone(process.fecha_inicio)
        self.assertIsNone(process.fecha_final)
        self.assertEqual(Process.objects.count(), 1)
        self.assertEqual(self.user.processes.count(), 1)
        self.assertEqual(self.process_type.processes.count(), 1)
        self.assertEqual(self.process_status.processes.count(), 1)

    def test_process_string_representation(self):
        """Test the string representation."""
        process = Process.objects.create(
            user=self.user,
            process_type=self.process_type,
            estado=self.process_status,
        )
        expected_string = "Asesoría for procuser - Status: En Progreso"
        self.assertEqual(str(process), expected_string)


class EquipmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="equipuser", password="password")
        # Optional: Create related objects if needed for multiple tests
        # self.process_type = ProcessType.objects.create(process_type=ProcessTypeChoices.ASESORIA)
        # self.process_status = ProcessStatus.objects.create(estado=ProcessStatusChoices.EN_PROGRESO)
        # self.process = Process.objects.create(
        #     user=self.user, process_type=self.process_type, estado=self.process_status
        # )

    def test_equipment_creation(self):
        """Test equipment creation."""
        equipment = Equipment.objects.create(
            nombre="Equipo Gamma",
            marca="MarcaX",
            modelo="ModeloY",
            serial="XYZ123",
            user=self.user,
        )
        self.assertEqual(equipment.nombre, "Equipo Gamma")
        self.assertEqual(equipment.serial, "XYZ123")
        self.assertEqual(equipment.user, self.user)
        self.assertFalse(equipment.tiene_proceso_de_asesoria)
        self.assertEqual(Equipment.objects.count(), 1)
        self.assertEqual(self.user.equipment.count(), 1)

    def test_equipment_creation_minimal(self):
        """Test equipment creation with minimal data."""
        equipment = Equipment.objects.create(nombre="Detector Simple")
        self.assertEqual(equipment.nombre, "Detector Simple")
        self.assertIsNone(equipment.serial)
        self.assertIsNone(equipment.user)
        self.assertEqual(Equipment.objects.count(), 1)

    def test_equipment_string_representation(self):
        """Test the string representation."""
        equipment_with_user = Equipment.objects.create(
            nombre="Equipo A", serial="SERA", user=self.user
        )
        equipment_no_user = Equipment.objects.create(nombre="Equipo B")
        equipment_no_serial = Equipment.objects.create(
            nombre="Equipo C", user=self.user
        )

        expected_str_1 = "Equipo A (SERA) - Owner: equipuser"
        expected_str_2 = "Equipo B (No Serial) - Owner: None"
        expected_str_3 = "Equipo C (No Serial) - Owner: equipuser"

        self.assertEqual(str(equipment_with_user), expected_str_1)
        self.assertEqual(str(equipment_no_user), expected_str_2)
        self.assertEqual(str(equipment_no_serial), expected_str_3)

    def test_equipment_serial_uniqueness(self):
        """Test that non-null equipment serial numbers must be unique."""
        Equipment.objects.create(nombre="Equipo 1", serial="UNIQUE123")
        # Ensure the first one was created successfully before attempting the duplicate
        self.assertEqual(Equipment.objects.count(), 1)
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(nombre="Equipo 2", serial="UNIQUE123")
        # No need to check count again here, as the transaction might be broken
        # if the IntegrityError occurred as expected. The assertRaises handles the check.

    def test_equipment_null_serial_allowed(self):
        """Test that multiple equipment items can have a null serial."""
        Equipment.objects.create(nombre="Equipo 3", serial=None)
        Equipment.objects.create(nombre="Equipo 4", serial=None)
        # Check that both were created successfully
        self.assertEqual(Equipment.objects.count(), 2)

    def test_unique_serial_validation(self):
        """Non-null serial must be unique at validation time."""
        eq1 = Equipment(nombre="E1", serial="ABC123")
        eq1.full_clean()
        eq1.save()

        eq2 = Equipment(nombre="E2", serial="ABC123")
        with self.assertRaises(ValidationError):
            eq2.full_clean()

    def test_serial_blank_allowed_validation(self):
        """Null serial should pass model validation repeatedly."""
        eq1 = Equipment(nombre="E1", serial=None)
        eq2 = Equipment(nombre="E2", serial=None)
        # both should validate without error
        eq1.full_clean()
        eq2.full_clean()
        eq1.save()
        eq2.save()
        self.assertEqual(Equipment.objects.count(), 2)


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
