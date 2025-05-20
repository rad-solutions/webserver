import os
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase

from ..models import ClientProfile  # Changed from .models
from ..models import EstadoEquipoChoices  # Changed from .models
from ..models import EstadoReporteChoices  # Changed from .models
from ..models import (  # Changed from .models
    Equipment,
    Process,
    ProcessStatusChoices,
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
        expected_string = f"{self.user.first_name} {self.user.last_name} ({self.user.email or self.user.username})"
        self.assertEqual(str(self.user), expected_string)

    def test_user_string_representation_no_name_email(self):
        """Test string representation when first/last name and email are missing."""
        user_only_username = User.objects.create_user(
            username="onlyuser", password="password"
        )
        self.assertEqual(str(user_only_username), "onlyuser")

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
        # Removed ProcessType and ProcessStatus creation as they are no longer models
        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,  # Directly use choice
            estado=ProcessStatusChoices.EN_PROGRESO,  # Directly use choice
        )

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"contenido de prueba del PDF")
        self.temp_file.close()

        with open(self.temp_file.name, "rb") as pdf:
            self.report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe de prueba",
                description="Esta es una descripción de prueba",
                pdf_file=SimpleUploadedFile("test.pdf", pdf.read()),
                estado_reporte=EstadoReporteChoices.EN_GENERACION,
            )

    def tearDown(self):
        os.unlink(self.temp_file.name)
        if self.report.pdf_file and os.path.exists(
            self.report.pdf_file.path
        ):  # Check if pdf_file exists before accessing path
            os.unlink(self.report.pdf_file.path)

    def test_report_creation(self):
        """Test que la creación de un informe funciona correctamente"""
        self.assertEqual(self.report.user, self.user)
        self.assertEqual(self.report.process, self.process)
        self.assertEqual(self.report.title, "Informe de prueba")
        self.assertEqual(self.report.description, "Esta es una descripción de prueba")
        self.assertTrue(self.report.pdf_file)
        self.assertTrue(self.report.created_at is not None)
        self.assertEqual(self.report.estado_reporte, EstadoReporteChoices.EN_GENERACION)
        self.assertIsNone(self.report.fecha_vencimiento)

    def test_report_string_representation(self):
        expected_string = "Report by Test: Informe de prueba"
        self.assertEqual(str(self.report), expected_string)

    def test_user_reports_relationship(self):
        self.assertEqual(self.user.reports.count(), 1)
        self.assertEqual(self.user.reports.first(), self.report)

    def test_process_reports_relationship(self):
        self.assertEqual(self.process.reports.count(), 1)
        self.assertEqual(self.process.reports.first(), self.report)

    def test_missing_title_validation(self):
        """Cannot create report without title."""
        rpt = Report(
            user=self.user,
            process=self.process,
            description="No title provided",
            pdf_file=SimpleUploadedFile("no_title.pdf", b"data"),
        )
        with self.assertRaises(ValidationError):
            rpt.full_clean()

    def test_missing_pdf_validation(self):
        """Cannot create report without PDF file."""
        rpt = Report(
            user=self.user,
            process=self.process,
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

        role_director = Role.objects.create(name=RoleChoices.DIRECTOR_TECNICO)
        self.assertEqual(role_director.name, "director_tecnico")

    def test_role_string_representation(self):
        """Test the string representation of the role."""
        role = Role.objects.create(name=RoleChoices.GERENTE)
        self.assertEqual(str(role), "Gerente")

    def test_role_uniqueness(self):
        """Test that role names must be unique."""
        Role.objects.create(name=RoleChoices.CLIENTE)
        with self.assertRaises(IntegrityError):
            Role.objects.create(name=RoleChoices.CLIENTE)


# Removed ProcessTypeModelTest and ProcessStatusModelTest as these models were removed


class ProcessModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="procuser", password="password")
        # ProcessType and ProcessStatus are now CharFields with choices, no need to create separate objects

    def test_process_creation(self):
        """Test process creation and relationships."""
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,  # Use choice directly
            estado=ProcessStatusChoices.EN_PROGRESO,  # Use choice directly
        )
        self.assertEqual(process.user, self.user)
        self.assertEqual(process.process_type, ProcessTypeChoices.ASESORIA)
        self.assertEqual(process.estado, ProcessStatusChoices.EN_PROGRESO)
        self.assertIsNotNone(process.fecha_inicio)
        self.assertIsNone(process.fecha_final)
        self.assertEqual(Process.objects.count(), 1)
        self.assertEqual(self.user.processes.count(), 1)
        # No longer applicable: self.assertEqual(self.process_type.processes.count(), 1)
        # No longer applicable: self.assertEqual(self.process_status.processes.count(), 1)

    def test_process_string_representation(self):
        """Test the string representation."""
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        # The string representation might change as it was using get_process_type_display() and get_estado_display()
        # Assuming the __str__ method in Process model is updated to handle CharField directly
        # or you might want to test the raw value or a new display method.
        # For now, let's assume it returns the choice value directly or its display name.
        # This test might need adjustment based on the Process model's __str__ method.
        expected_string = f"{ProcessTypeChoices.ASESORIA.label} for procuser - Status: {ProcessStatusChoices.EN_PROGRESO.label}"
        self.assertEqual(str(process), expected_string)


class EquipmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="equipuser", password="password")
        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )

    def test_equipment_creation(self):
        """Test equipment creation."""
        equipment = Equipment.objects.create(
            nombre="Equipo Gamma",
            marca="MarcaX",
            modelo="ModeloY",
            serial="XYZ123",
            user=self.user,
            estado_actual=EstadoEquipoChoices.EN_USO,
            sede="Sede Principal",
        )
        self.assertEqual(equipment.nombre, "Equipo Gamma")
        self.assertEqual(equipment.serial, "XYZ123")
        self.assertEqual(equipment.user, self.user)
        self.assertFalse(equipment.tiene_proceso_de_asesoria)
        self.assertEqual(equipment.estado_actual, EstadoEquipoChoices.EN_USO)
        self.assertEqual(equipment.sede, "Sede Principal")
        self.assertEqual(Equipment.objects.count(), 1)
        self.assertEqual(self.user.equipment.count(), 1)

    def test_equipment_creation_minimal(self):
        """Test equipment creation with minimal data."""
        Equipment.objects.all().delete()
        equipment = Equipment.objects.create(nombre="Detector Simple")
        self.assertEqual(equipment.nombre, "Detector Simple")
        self.assertIsNone(equipment.serial)
        self.assertIsNone(equipment.user)
        self.assertEqual(equipment.estado_actual, EstadoEquipoChoices.EN_USO)
        self.assertIsNone(equipment.sede)
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
        Equipment.objects.all().delete()
        Equipment.objects.create(nombre="Equipo 1", serial="UNIQUE123")
        self.assertEqual(Equipment.objects.count(), 1)
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(nombre="Equipo 2", serial="UNIQUE123")

    def test_equipment_null_serial_allowed(self):
        """Test that multiple equipment items can have a null serial."""
        Equipment.objects.all().delete()
        Equipment.objects.create(nombre="Equipo 3", serial=None)
        Equipment.objects.create(nombre="Equipo 4", serial=None)
        self.assertEqual(Equipment.objects.count(), 2)

    def test_unique_serial_validation(self):
        """Non-null serial must be unique at validation time."""
        Equipment.objects.all().delete()
        eq1 = Equipment(nombre="E1", serial="ABC123")
        eq1.full_clean()
        eq1.save()

        eq2 = Equipment(nombre="E2", serial="ABC123")
        with self.assertRaises(ValidationError):
            eq2.full_clean()

    def test_serial_blank_allowed_validation(self):
        """Null serial should pass model validation repeatedly."""
        Equipment.objects.all().delete()
        eq1 = Equipment(nombre="E1", serial=None)
        eq2 = Equipment(nombre="E2", serial=None)
        eq1.full_clean()
        eq2.full_clean()
        eq1.save()
        eq2.save()
        self.assertEqual(Equipment.objects.count(), 2)


class ClientProfileModelTest(TestCase):
    def setUp(self):
        self.user_client = User.objects.create_user(
            username="clientuser",
            password="password",
            first_name="Client",
            last_name="User",
        )
        Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.user_client.roles.add(Role.objects.get(name=RoleChoices.CLIENTE))

    def test_client_profile_creation(self):
        profile = ClientProfile.objects.create(
            user=self.user_client,
            razon_social="Empresa XYZ S.A.S.",
            nit="900123456-7",
            direccion_instalacion="Calle Falsa 123",
            departamento="Antioquia",
            municipio="Medellín",
        )
        self.assertEqual(profile.user, self.user_client)
        self.assertEqual(profile.razon_social, "Empresa XYZ S.A.S.")
        self.assertEqual(profile.nit, "900123456-7")
        self.assertEqual(str(profile), "Empresa XYZ S.A.S. (900123456-7)")
        self.assertEqual(ClientProfile.objects.count(), 1)
        self.assertEqual(self.user_client.client_profile, profile)

    def test_client_profile_nit_uniqueness(self):
        ClientProfile.objects.create(
            user=self.user_client,
            razon_social="Empresa A",
            nit="111222333-1",
            direccion_instalacion="Dir A",
            departamento="Dep A",
            municipio="Mun A",
        )
        another_user = User.objects.create_user(
            username="anotherclient", password="password"
        )
        with self.assertRaises(IntegrityError):
            ClientProfile.objects.create(
                user=another_user,
                razon_social="Empresa B",
                nit="111222333-1",
                direccion_instalacion="Dir B",
                departamento="Dep B",
                municipio="Mun B",
            )

    def test_one_to_one_user_constraint(self):
        ClientProfile.objects.create(
            user=self.user_client,
            razon_social="Empresa C",
            nit="444555666-1",
            direccion_instalacion="Dir C",
            departamento="Dep C",
            municipio="Mun C",
        )
        with self.assertRaises(IntegrityError):
            ClientProfile.objects.create(
                user=self.user_client,
                razon_social="Empresa D",
                nit="777888999-1",
                direccion_instalacion="Dir D",
                departamento="Dep D",
                municipio="Mun D",
            )
