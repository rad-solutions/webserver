import os
import tempfile
from datetime import date, datetime, timedelta, timezone

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.urls import reverse

from .models import ClientProfile  # Added
from .models import EstadoEquipoChoices  # Added
from .models import EstadoReporteChoices  # Added
from .models import (
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
        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"contenido de prueba del PDF")
        self.temp_file.close()

        with open(self.temp_file.name, "rb") as pdf:
            self.report = Report.objects.create(
                user=self.user,
                process=self.process,  # Added process
                title="Informe de prueba",
                description="Esta es una descripción de prueba",
                pdf_file=SimpleUploadedFile("test.pdf", pdf.read()),
                estado_reporte=EstadoReporteChoices.EN_GENERACION,  # Added
            )

    def tearDown(self):
        os.unlink(self.temp_file.name)
        if os.path.exists(self.report.pdf_file.path):
            os.unlink(self.report.pdf_file.path)

    def test_report_creation(self):
        """Test que la creación de un informe funciona correctamente"""
        self.assertEqual(self.report.user, self.user)
        self.assertEqual(self.report.process, self.process)  # Added
        self.assertEqual(self.report.title, "Informe de prueba")
        self.assertEqual(self.report.description, "Esta es una descripción de prueba")
        self.assertTrue(self.report.pdf_file)
        self.assertTrue(self.report.created_at is not None)
        self.assertEqual(
            self.report.estado_reporte, EstadoReporteChoices.EN_GENERACION
        )  # Added
        self.assertIsNone(self.report.fecha_vencimiento)  # Added

    def test_report_string_representation(self):
        expected_string = "Report by Test: Informe de prueba"
        self.assertEqual(str(self.report), expected_string)

    def test_user_reports_relationship(self):
        self.assertEqual(self.user.reports.count(), 1)
        self.assertEqual(self.user.reports.first(), self.report)

    def test_process_reports_relationship(self):  # Added
        self.assertEqual(self.process.reports.count(), 1)
        self.assertEqual(self.process.reports.first(), self.report)

    def test_missing_title_validation(self):
        """Cannot create report without title."""
        rpt = Report(
            user=self.user,
            process=self.process,  # Added
            description="No title provided",
            pdf_file=SimpleUploadedFile("no_title.pdf", b"data"),
        )
        with self.assertRaises(ValidationError):
            rpt.full_clean()

    def test_missing_pdf_validation(self):
        """Cannot create report without PDF file."""
        rpt = Report(
            user=self.user,
            process=self.process,  # Added
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


class ProcessModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="procuser", password="password")
        self.process_type = ProcessTypeChoices.ASESORIA
        self.process_status = ProcessStatusChoices.EN_PROGRESO

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

    def test_process_string_representation(self):
        """Test the string representation."""
        process = Process.objects.create(
            user=self.user,
            process_type=self.process_type,
            estado=self.process_status,
        )
        expected_string = "asesoria for procuser - Status: en_progreso"
        self.assertEqual(str(process), expected_string)


class EquipmentModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="equipuser", password="password")
        # Optional: Create related objects if needed for multiple tests
        self.process_type = ProcessTypeChoices.ASESORIA
        self.process_status = ProcessStatusChoices.EN_PROGRESO
        self.process = Process.objects.create(
            user=self.user, process_type=self.process_type, estado=self.process_status
        )

    def test_equipment_creation(self):
        """Test equipment creation."""
        equipment = Equipment.objects.create(
            nombre="Equipo Gamma",
            marca="MarcaX",
            modelo="ModeloY",
            serial="XYZ123",
            user=self.user,
            estado_actual=EstadoEquipoChoices.EN_USO,  # Added
            sede="Sede Principal",  # Added
        )
        self.assertEqual(equipment.nombre, "Equipo Gamma")
        self.assertEqual(equipment.serial, "XYZ123")
        self.assertEqual(equipment.user, self.user)
        self.assertFalse(equipment.tiene_proceso_de_asesoria)
        self.assertEqual(equipment.estado_actual, EstadoEquipoChoices.EN_USO)  # Added
        self.assertEqual(equipment.sede, "Sede Principal")  # Added
        self.assertEqual(Equipment.objects.count(), 1)
        self.assertEqual(self.user.equipment.count(), 1)

    def test_equipment_creation_minimal(self):
        """Test equipment creation with minimal data."""
        Equipment.objects.all().delete()  # Clear existing
        equipment = Equipment.objects.create(nombre="Detector Simple")
        self.assertEqual(equipment.nombre, "Detector Simple")
        self.assertIsNone(equipment.serial)
        self.assertIsNone(equipment.user)
        self.assertEqual(equipment.estado_actual, EstadoEquipoChoices.EN_USO)  # Default
        self.assertIsNone(equipment.sede)  # Default
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
        Equipment.objects.all().delete()  # Clear existing
        Equipment.objects.create(nombre="Equipo 1", serial="UNIQUE123")
        # Ensure the first one was created successfully before attempting the duplicate
        self.assertEqual(Equipment.objects.count(), 1)
        with self.assertRaises(IntegrityError):
            Equipment.objects.create(nombre="Equipo 2", serial="UNIQUE123")
        # No need to check count again here, as the transaction might be broken
        # if the IntegrityError occurred as expected. The assertRaises handles the check.

    def test_equipment_null_serial_allowed(self):
        """Test that multiple equipment items can have a null serial."""
        Equipment.objects.all().delete()  # Clear existing
        Equipment.objects.create(nombre="Equipo 3", serial=None)
        Equipment.objects.create(nombre="Equipo 4", serial=None)
        # Check that both were created successfully
        self.assertEqual(Equipment.objects.count(), 2)

    def test_unique_serial_validation(self):
        """Non-null serial must be unique at validation time."""
        Equipment.objects.all().delete()  # Clear existing
        eq1 = Equipment(nombre="E1", serial="ABC123")
        eq1.full_clean()
        eq1.save()

        eq2 = Equipment(nombre="E2", serial="ABC123")
        with self.assertRaises(ValidationError):
            eq2.full_clean()

    def test_serial_blank_allowed_validation(self):
        """Null serial should pass model validation repeatedly."""
        Equipment.objects.all().delete()  # Clear existing
        eq1 = Equipment(nombre="E1", serial=None)
        eq2 = Equipment(nombre="E2", serial=None)
        # both should validate without error
        eq1.full_clean()
        eq2.full_clean()
        eq1.save()
        eq2.save()
        self.assertEqual(Equipment.objects.count(), 2)


class ClientProfileModelTest(TestCase):  # Added
    def setUp(self):
        self.user_client = User.objects.create_user(
            username="clientuser",
            password="password",
            first_name="Client",
            last_name="User",
        )
        Role.objects.get_or_create(name=RoleChoices.CLIENTE)  # Ensure role exists
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
                nit="111222333-1",  # Duplicate NIT
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
        with self.assertRaises(
            IntegrityError
        ):  # Cannot create another profile for the same user
            ClientProfile.objects.create(
                user=self.user_client,
                razon_social="Empresa D",
                nit="777888999-1",
                direccion_instalacion="Dir D",
                departamento="Dep D",
                municipio="Mun D",
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
        # Asignar rol de cliente para probar el filtrado por usuario en ReportListView
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)
        self.user.roles.add(self.role_cliente)

        self.admin_user = User.objects.create_user(
            username="adminuser",
            email="admin@example.com",
            password="adminpassword",
            first_name="Admin",
            last_name="User",
            is_staff=True,
        )

        self.temp_file = tempfile.NamedTemporaryFile(suffix=".pdf", delete=False)
        self.temp_file.write(b"contenido de prueba del PDF")
        self.temp_file.close()

        self.process_type_asesoria = ProcessTypeChoices.ASESORIA
        self.process_type_calidad = ProcessTypeChoices.CONTROL_CALIDAD
        self.process_status_progreso = ProcessStatusChoices.EN_PROGRESO

        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )

        self.process_asesoria = Process.objects.create(
            user=self.user,
            process_type=self.process_type_asesoria,
            estado=self.process_status_progreso,
            fecha_inicio=datetime(2024, 1, 10, tzinfo=timezone.utc),
        )
        self.process_calidad = Process.objects.create(
            user=self.user,
            process_type=self.process_type_calidad,
            estado=self.process_status_progreso,
            fecha_inicio=datetime(2024, 2, 15, tzinfo=timezone.utc),
        )
        # Proceso para otro usuario (admin en este caso, para probar que no se listen sus reportes para el cliente)
        self.process_admin = Process.objects.create(
            user=self.admin_user,
            process_type=self.process_type_asesoria,
            estado=self.process_status_progreso,
            fecha_inicio=datetime(2024, 3, 1, tzinfo=timezone.utc),
        )

        self.temp_file_content = b"contenido de prueba del PDF"
        self.temp_file_name = "test.pdf"

        # Crear reportes con diferentes fechas de creación y tipos de proceso
        self.report1_asesoria_jan = Report.objects.create(
            user=self.user,
            process=self.process_asesoria,
            title="Reporte Asesoria Enero",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
        )
        # Forzar created_at para pruebas de filtro de fecha precisas
        self.report1_asesoria_jan.created_at = datetime(
            2024, 1, 15, 10, 0, 0, tzinfo=timezone.utc
        )
        self.report1_asesoria_jan.save()

        self.report2_calidad_feb = Report.objects.create(
            user=self.user,
            process=self.process_calidad,
            title="Reporte Calidad Febrero",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.REVISADO,
        )
        self.report2_calidad_feb.created_at = datetime(
            2024, 2, 20, 11, 0, 0, tzinfo=timezone.utc
        )
        self.report2_calidad_feb.save()

        self.report3_asesoria_mar = Report.objects.create(
            user=self.user,
            process=self.process_asesoria,
            title="Reporte Asesoria Marzo",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.APROBADO,
        )
        self.report3_asesoria_mar.created_at = datetime(
            2024, 3, 25, 12, 0, 0, tzinfo=timezone.utc
        )
        self.report3_asesoria_mar.save()

        # Reporte para el admin_user, no debería aparecer para el cliente
        self.report_admin_user = Report.objects.create(
            user=self.admin_user,
            process=self.process_admin,
            title="Reporte del Admin",
            pdf_file=SimpleUploadedFile(self.temp_file_name, self.temp_file_content),
            estado_reporte=EstadoReporteChoices.APROBADO,
        )
        self.report_admin_user.created_at = datetime(
            2024, 3, 10, 10, 0, 0, tzinfo=timezone.utc
        )
        self.report_admin_user.save()

    def tearDown(self):
        self.temp_file.close()
        if os.path.exists(self.temp_file.name):
            os.unlink(self.temp_file.name)

        for report in Report.objects.all():
            if report.pdf_file and hasattr(report.pdf_file, "path"):
                if os.path.exists(report.pdf_file.path):
                    try:
                        os.remove(report.pdf_file.path)
                    except OSError:
                        pass

    def test_report_list_view(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            Report.objects.create(
                user=self.user,
                process=self.process,
                title="Reporte en lista",
                pdf_file=SimpleUploadedFile("list.pdf", temp_file.read()),
                estado_reporte=EstadoReporteChoices.EN_GENERACION,
            )
            temp_file.seek(0)

        url = reverse("report_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_list.html")
        self.assertIn("reports", response.context)

    def test_report_detail_view(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Detalle Reporte",
                pdf_file=SimpleUploadedFile("detail.pdf", temp_file.read()),
                estado_reporte=EstadoReporteChoices.EN_GENERACION,
            )
            temp_file.seek(0)
        url = reverse("report_detail", args=[report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_detail.html")
        self.assertEqual(response.context["report"], report)

    def test_report_create_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_form.html")
        self.assertIn("form", response.context)

    def test_report_create_view_post_valid(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()
        with open(self.temp_file.name, "rb") as pdf:
            data = {
                "title": "Nuevo informe de prueba",
                "description": "Descripción del nuevo informe",
                "pdf_file": pdf,
                "process": self.process.id,
                "user": self.user.id,
                "estado_reporte": EstadoReporteChoices.EN_GENERACION,
                "fecha_vencimiento": date.today() + timedelta(days=30),
            }
            response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Report.objects.count(), initial_count + 1)
        self.assertRedirects(response, reverse("report_list"))
        new_report = Report.objects.latest("created_at")
        self.assertEqual(new_report.title, "Nuevo informe de prueba")
        self.assertEqual(new_report.user, self.user)

    def test_report_create_view_post_invalid_no_title(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()
        with open(self.temp_file.name, "rb") as pdf:
            data = {
                "description": "Este informe no tiene título",
                "pdf_file": pdf,
                "process": self.process.id,
                "user": self.user.id,
                "estado_reporte": EstadoReporteChoices.EN_GENERACION,
            }
            response = self.client.post(url, data, format="multipart")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Report.objects.count(), initial_count)
        self.assertIn("form", response.context)
        self.assertTrue(response.context["form"].errors)
        form_in_context = response.context.get("form")
        self.assertIsNotNone(
            form_in_context,
            "El formulario no se encontró en el contexto de la respuesta.",
        )
        self.assertFormError(form_in_context, "title", "This field is required.")

    def test_report_create_view_post_invalid_no_pdf(self):
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_create")
        initial_count = Report.objects.count()
        data = {
            "title": "Informe sin archivo",
            "description": "Este informe no tiene archivo PDF",
            "process": self.process.id,
            "user": self.user.id,
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Report.objects.count(), initial_count)
        form_in_context = response.context.get("form")
        self.assertIsNotNone(
            form_in_context,
            "El formulario no se encontró en el contexto de la respuesta.",
        )
        self.assertFormError(form_in_context, "pdf_file", "This field is required.")

    def test_report_update_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Para Actualizar GET",
                pdf_file=SimpleUploadedFile("update_get.pdf", temp_file.read()),
            )
            temp_file.seek(0)
        url = reverse("report_update", args=[report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_form.html")
        self.assertEqual(response.context["form"].instance, report)

    def test_report_update_view_post_valid(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe para actualizar",
                description="Descripción original",
                pdf_file=SimpleUploadedFile("update_me.pdf", temp_file.read()),
                estado_reporte=EstadoReporteChoices.EN_GENERACION,
            )
            temp_file.seek(0)

        url = reverse("report_update", args=[report.id])
        updated_title = "Título actualizado"
        updated_description = "Descripción actualizada"
        updated_estado = EstadoReporteChoices.REVISADO

        # Para actualizar un FileField, necesitas pasar un nuevo archivo.
        # Si no se pasa, el archivo existente se mantiene.
        # Si quieres probar la actualización del archivo, crea otro archivo temporal.
        with open(self.temp_file.name, "rb") as pdf_update:
            data = {
                "title": updated_title,
                "description": updated_description,
                "process": self.process.id,
                "user": self.user.id,
                "estado_reporte": updated_estado,
                "pdf_file": pdf_update,
            }
            response = self.client.post(url, data, format="multipart")

        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("report_list"))

        report.refresh_from_db()
        self.assertEqual(report.title, updated_title)
        self.assertEqual(report.description, updated_description)
        self.assertEqual(report.estado_reporte, updated_estado)

    def test_report_delete_view_get(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Para Eliminar GET",
                pdf_file=SimpleUploadedFile("delete_get.pdf", temp_file.read()),
            )
            temp_file.seek(0)
        url = reverse("report_delete", args=[report.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_confirm_delete.html")
        self.assertEqual(response.context["report"], report)

    def test_report_delete_view_post(self):
        self.client.login(username="testuser", password="testpassword")
        with open(self.temp_file.name, "rb") as temp_file:
            report = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe para eliminar",
                description="Este informe será eliminado",
                pdf_file=SimpleUploadedFile("delete_me.pdf", temp_file.read()),
            )
            temp_file.seek(0)
        initial_count = Report.objects.count()

        url = reverse("report_delete", args=[report.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertRedirects(response, reverse("report_list"))
        self.assertEqual(Report.objects.count(), initial_count - 1)
        with self.assertRaises(Report.DoesNotExist):
            Report.objects.get(id=report.id)

    def test_report_list_view_no_filters_client_user(self):
        """Test ReportListView sin filtros para un usuario cliente."""
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "reports/report_list.html")
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 3)  # Solo los del self.user
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertIn(self.report3_asesoria_mar, reports_in_context)
        self.assertNotIn(
            self.report_admin_user, reports_in_context
        )  # No debe mostrar el del admin
        self.assertEqual(response.context["selected_process_type"], "todos")
        self.assertEqual(response.context["start_date"], "")
        self.assertEqual(response.context["end_date"], "")

    def test_report_list_view_no_filters_admin_user(self):
        """Test ReportListView sin filtros para un usuario admin (debería ver todos)."""
        self.client.login(username="adminuser", password="adminpassword")
        url = reverse("report_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 4)  # Todos los reportes
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertIn(self.report_admin_user, reports_in_context)

    def test_report_list_view_filter_by_process_type(self):
        """Test ReportListView filtrando por tipo de proceso."""
        self.client.login(username="testuser", password="testpassword")
        url = reverse("report_list") + f"?process_type={self.process_type_asesoria}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 2)
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertIn(self.report3_asesoria_mar, reports_in_context)
        self.assertNotIn(self.report2_calidad_feb, reports_in_context)
        self.assertEqual(
            response.context["selected_process_type"], self.process_type_asesoria
        )

    def test_report_list_view_filter_by_start_date(self):
        """Test ReportListView filtrando por fecha de inicio."""
        self.client.login(username="testuser", password="testpassword")
        # Filtra reportes creados desde el 1 de Febrero de 2024
        start_date_filter = "2024-02-01"
        url = reverse("report_list") + f"?start_date={start_date_filter}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(
            len(reports_in_context), 2
        )  # report2_calidad_feb y report3_asesoria_mar
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertIn(self.report3_asesoria_mar, reports_in_context)
        self.assertNotIn(self.report1_asesoria_jan, reports_in_context)
        self.assertEqual(response.context["start_date"], start_date_filter)

    def test_report_list_view_filter_by_end_date(self):
        """Test ReportListView filtrando por fecha de fin."""
        self.client.login(username="testuser", password="testpassword")
        # Filtra reportes creados hasta el 28 de Febrero de 2024
        end_date_filter = "2024-02-28"
        url = reverse("report_list") + f"?end_date={end_date_filter}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(
            len(reports_in_context), 2
        )  # report1_asesoria_jan y report2_calidad_feb
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertNotIn(self.report3_asesoria_mar, reports_in_context)
        self.assertEqual(response.context["end_date"], end_date_filter)

    def test_report_list_view_filter_by_date_range(self):
        """Test ReportListView filtrando por rango de fechas."""
        self.client.login(username="testuser", password="testpassword")
        start_date_filter = "2024-02-01"
        end_date_filter = "2024-02-29"  # Incluye todo Febrero
        url = (
            reverse("report_list")
            + f"?start_date={start_date_filter}&end_date={end_date_filter}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 1)  # Solo report2_calidad_feb
        self.assertIn(self.report2_calidad_feb, reports_in_context)
        self.assertNotIn(self.report1_asesoria_jan, reports_in_context)
        self.assertNotIn(self.report3_asesoria_mar, reports_in_context)
        self.assertEqual(response.context["start_date"], start_date_filter)
        self.assertEqual(response.context["end_date"], end_date_filter)

    def test_report_list_view_filter_by_process_type_and_date_range(self):
        """Test ReportListView filtrando por tipo de proceso y rango de fechas."""
        self.client.login(username="testuser", password="testpassword")
        process_type_filter = self.process_type_asesoria
        start_date_filter = "2024-01-01"
        end_date_filter = "2024-01-31"  # Solo Enero
        url = (
            reverse("report_list")
            + f"?process_type={process_type_filter}&start_date={start_date_filter}&end_date={end_date_filter}"
        )
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 1)  # Solo report1_asesoria_jan
        self.assertIn(self.report1_asesoria_jan, reports_in_context)
        self.assertNotIn(self.report2_calidad_feb, reports_in_context)
        self.assertNotIn(self.report3_asesoria_mar, reports_in_context)
        self.assertEqual(response.context["selected_process_type"], process_type_filter)
        self.assertEqual(response.context["start_date"], start_date_filter)
        self.assertEqual(response.context["end_date"], end_date_filter)

    def test_report_list_view_filter_no_results(self):
        """Test ReportListView con filtros que no devuelven resultados."""
        self.client.login(username="testuser", password="testpassword")
        start_date_filter = "2025-01-01"  # Fecha futura sin reportes
        url = reverse("report_list") + f"?start_date={start_date_filter}"
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        reports_in_context = response.context["reports"]
        self.assertEqual(len(reports_in_context), 0)
        self.assertEqual(response.context["start_date"], start_date_filter)


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


class ClientDashboardTest(TestCase):
    def setUp(self):
        # Crear roles si no existen
        self.role_cliente, _ = Role.objects.get_or_create(name=RoleChoices.CLIENTE)

        # Crear un usuario cliente
        self.user = User.objects.create_user(
            username="clientuser",
            email="client@example.com",
            password="testpassword",
            first_name="Client",
            last_name="User",
        )
        self.user.roles.add(self.role_cliente)

        # Crear tipos de proceso (usando los valores de ProcessTypeChoices)
        self.process_type_blindajes = ProcessTypeChoices.CALCULO_BLINDAJES
        self.process_type_calidad = ProcessTypeChoices.CONTROL_CALIDAD
        self.process_type_asesoria = ProcessTypeChoices.ASESORIA

        # Crear estado de proceso
        self.process_status = ProcessStatusChoices.EN_PROGRESO

        # Crear procesos para el usuario
        self.process_blindajes = Process.objects.create(
            user=self.user,
            process_type=self.process_type_blindajes,
            estado=self.process_status,
        )
        self.process_calidad = Process.objects.create(
            user=self.user,
            process_type=self.process_type_calidad,
            estado=self.process_status,
        )
        self.process_asesoria = Process.objects.create(
            user=self.user,
            process_type=self.process_type_asesoria,
            estado=self.process_status,
        )

        # Crear un archivo PDF temporal para los reportes
        self.temp_pdf_file_content = b"dummy pdf content"
        self.temp_pdf_file_name = "test_report.pdf"

        # Crear reportes asociados a los procesos
        self.report_blindajes = Report.objects.create(
            user=self.user,
            process=self.process_blindajes,
            title="Reporte Blindajes",
            description="Descripción del reporte de blindajes",
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
            pdf_file=SimpleUploadedFile(
                self.temp_pdf_file_name, self.temp_pdf_file_content
            ),
        )
        self.report_calidad = Report.objects.create(
            user=self.user,
            process=self.process_calidad,
            title="Reporte Calidad",
            description="Descripción del reporte de calidad",
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
            pdf_file=SimpleUploadedFile(
                self.temp_pdf_file_name, self.temp_pdf_file_content
            ),
        )
        self.report_asesoria = Report.objects.create(
            user=self.user,
            process=self.process_asesoria,
            title="Reporte Asesoria",
            description="Descripción del reporte de asesoría",
            estado_reporte=EstadoReporteChoices.EN_GENERACION,
            pdf_file=SimpleUploadedFile(
                self.temp_pdf_file_name, self.temp_pdf_file_content
            ),
        )

        # Crear equipos asociados a los procesos del usuario
        self.equipment_blindajes = Equipment.objects.create(
            nombre="Equipo Blindajes 1",
            marca="MarcaA",
            modelo="ModeloA1",
            serial="SN001",
            user=self.user,
            process=self.process_blindajes,
            fecha_vigencia_licencia="2025-12-31",
        )
        self.equipment_calidad = Equipment.objects.create(
            nombre="Equipo Calidad 1",
            marca="MarcaB",
            modelo="ModeloB1",
            serial="SN002",
            user=self.user,
            process=self.process_calidad,
            fecha_vigencia_licencia="2026-06-15",
        )
        # Equipo sin proceso para probar la sección de licencias por vencer
        self.equipment_licencia_proxima = Equipment.objects.create(
            nombre="Equipo Licencia Próxima",
            marca="MarcaC",
            modelo="ModeloC1",
            serial="SN003",
            user=self.user,
            fecha_vigencia_licencia=date.today()
            + timedelta(days=30),  # Licencia vence en 30 días
        )
        self.equipment_licencia_lejana = Equipment.objects.create(
            nombre="Equipo Licencia Lejana",
            marca="MarcaD",
            modelo="ModeloD1",
            serial="SN004",
            user=self.user,
            fecha_vigencia_licencia=date.today()
            + timedelta(days=365),  # Licencia vence en 1 año
        )

    def tearDown(self):
        # Limpiar archivos PDF creados por los reportes
        for report in Report.objects.all():
            if report.pdf_file and hasattr(report.pdf_file, "path"):
                if os.path.exists(report.pdf_file.path):
                    try:
                        os.remove(report.pdf_file.path)
                    except OSError:
                        pass

    def test_dashboard_initial_state_for_client(self):
        """Verificar el estado inicial del dashboard del cliente (sin proceso_activo)."""
        self.client.login(username="clientuser", password="testpassword")
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "dashboard_cliente.html")

        # Verificar claves de contexto principales
        self.assertIn("titulo", response.context)
        self.assertIn("mensaje_bienvenida", response.context)
        self.assertIn("equipos_licencia_por_vencer", response.context)
        self.assertIn("proceso_activo", response.context)
        self.assertIn("process_types_choices", response.context)
        self.assertIn("reportes", response.context)
        self.assertIn("equipos", response.context)

        # Verificar valores en el estado inicial
        self.assertIsNone(response.context["proceso_activo"])
        self.assertIsNone(response.context["reportes"])
        self.assertIsNone(response.context["equipos"])

        # Verificar equipos con licencia próxima a vencer
        equipos_vencer = response.context["equipos_licencia_por_vencer"]
        self.assertEqual(len(equipos_vencer), 1)
        self.assertIn(self.equipment_licencia_proxima, equipos_vencer)
        self.assertNotIn(self.equipment_licencia_lejana, equipos_vencer)
        self.assertNotIn(self.equipment_blindajes, equipos_vencer)

        self.assertEqual(
            response.context["process_types_choices"], list(ProcessTypeChoices.choices)
        )
        self.assertTrue(
            response.context["mensaje_bienvenida"].startswith("Bienvenido, Client")
        )

    def test_dashboard_with_proceso_activo_for_client(self):
        """Verificar el dashboard del cliente cuando se selecciona un proceso_activo."""
        self.client.login(username="clientuser", password="testpassword")

        # Probar con 'calculo_blindajes'
        url_blindajes = (
            reverse("home") + f"?proceso_activo={self.process_type_blindajes}"
        )
        response_blindajes = self.client.get(url_blindajes)

        self.assertEqual(response_blindajes.status_code, 200)
        self.assertTemplateUsed(response_blindajes, "dashboard_cliente.html")

        self.assertEqual(
            response_blindajes.context["proceso_activo"], self.process_type_blindajes
        )

        # Verificar reportes para calculo_blindajes (debería ser 1, y limitado a 5 por la vista)
        reportes_blindajes = response_blindajes.context["reportes"]
        self.assertIsNotNone(reportes_blindajes)
        self.assertEqual(len(reportes_blindajes), 1)
        self.assertIn(self.report_blindajes, reportes_blindajes)
        self.assertNotIn(self.report_calidad, reportes_blindajes)

        # Verificar equipos para calculo_blindajes (debería ser 1, y limitado a 5 por la vista)
        equipos_blindajes = response_blindajes.context["equipos"]
        self.assertIsNotNone(equipos_blindajes)
        self.assertEqual(len(equipos_blindajes), 1)
        self.assertIn(self.equipment_blindajes, equipos_blindajes)
        self.assertNotIn(self.equipment_calidad, equipos_blindajes)

        # Equipos con licencia próxima a vencer deben seguir presentes
        self.assertIn("equipos_licencia_por_vencer", response_blindajes.context)
        equipos_vencer_blindajes = response_blindajes.context[
            "equipos_licencia_por_vencer"
        ]
        self.assertEqual(len(equipos_vencer_blindajes), 1)
        self.assertIn(self.equipment_licencia_proxima, equipos_vencer_blindajes)

        # Probar con 'control_calidad'
        url_calidad = reverse("home") + f"?proceso_activo={self.process_type_calidad}"
        response_calidad = self.client.get(url_calidad)
        self.assertEqual(response_calidad.status_code, 200)
        self.assertEqual(
            response_calidad.context["proceso_activo"], self.process_type_calidad
        )

        reportes_calidad = response_calidad.context["reportes"]
        self.assertEqual(len(reportes_calidad), 1)
        self.assertIn(self.report_calidad, reportes_calidad)

        equipos_calidad = response_calidad.context["equipos"]
        self.assertEqual(len(equipos_calidad), 1)
        self.assertIn(self.equipment_calidad, equipos_calidad)

    def test_dashboard_non_client_user(self):
        """Verificar que un usuario no cliente es redirigido a main.html."""
        # Crear un usuario sin rol de cliente
        User.objects.create_user(
            username="staffuser", password="password", is_staff=True
        )
        self.client.login(username="staffuser", password="password")
        response = self.client.get(reverse("home"))

        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "main.html")
        self.assertNotIn("equipos_licencia_por_vencer", response.context)
        self.assertNotIn("process_types_choices", response.context)


class ProcessAPITest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(username="procuser", password="password")
        self.other_user = User.objects.create_user(
            username="otherprocuser", password="password"
        )
        self.client.login(username="procuser", password="password")

    def test_process_list_view(self):
        Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        url = reverse("process_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_list.html")
        self.assertIn("equipos", response.context)

    def test_process_detail_view(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.RADICADO,
        )
        url = reverse("process_detail", args=[process.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_detail.html")
        self.assertEqual(response.context["process"], process)

    def test_process_create_view_get(self):
        url = reverse("process_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_form.html")

    def test_process_create_view_post_valid(self):
        url = reverse("process_create")
        initial_count = Process.objects.count()
        data = {
            "user": self.user.id,
            "process_type": ProcessTypeChoices.CALCULO_BLINDAJES,
            "estado": ProcessStatusChoices.EN_PROGRESO,
            "fecha_final": (date.today() + timedelta(days=10)).strftime(
                "%Y-%m-%dT%H:%M"
            ),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Process.objects.count(), initial_count + 1)
        new_process = Process.objects.latest("fecha_inicio")
        self.assertEqual(new_process.user, self.user)
        self.assertEqual(new_process.process_type, ProcessTypeChoices.CALCULO_BLINDAJES)

    def test_process_create_view_post_invalid(self):
        url = reverse("process_create")
        initial_count = Process.objects.count()
        data = {"user": self.user.id, "estado": "estado_invalido"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Process.objects.count(), initial_count)
        self.assertTrue(response.context["form"].errors)

    def test_process_update_view_get(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        url = reverse("process_update", args=[process.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_form.html")
        self.assertEqual(response.context["form"].instance, process)

    def test_process_update_view_post_valid(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        url = reverse("process_update", args=[process.id])
        data = {
            "user": self.user.id,
            "process_type": ProcessTypeChoices.CONTROL_CALIDAD,
            "estado": ProcessStatusChoices.FINALIZADO,
            "fecha_final": date.today().strftime("%Y-%m-%dT%H:%M"),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        process.refresh_from_db()
        self.assertEqual(process.process_type, ProcessTypeChoices.CONTROL_CALIDAD)
        self.assertEqual(process.estado, ProcessStatusChoices.FINALIZADO)

    def test_process_delete_view_get(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.RADICADO,
        )
        url = reverse("process_delete", args=[process.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "process/process_confirm_delete.html")

    def test_process_delete_view_post(self):
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.OTRO,
            estado=ProcessStatusChoices.RADICADO,
        )
        initial_count = Process.objects.count()
        url = reverse("process_delete", args=[process.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Process.objects.count(), initial_count - 1)


class EquipmentAPITest(TestCase):
    def setUp(self):
        self.user_client = User.objects.create_user(
            username="equipclient",
            password="password",
            first_name="Equip",
            last_name="Client",
        )
        self.admin_user = User.objects.create_user(
            username="equipadmin", password="password", is_staff=True
        )
        self.process = Process.objects.create(
            user=self.user_client,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.client.login(username="equipadmin", password="password")

    def test_equipment_list_view(self):
        Equipment.objects.create(
            nombre="Equipo en Lista", user=self.user_client, process=self.process
        )
        url = reverse("equipos_list")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_list.html")
        self.assertIn("equipos", response.context)

    def test_equipment_detail_view(self):
        equipment = Equipment.objects.create(
            nombre="Detalle Equipo", user=self.user_client, process=self.process
        )
        url = reverse("equipos_detail", args=[equipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_detail.html")
        self.assertEqual(response.context["equipo"], equipment)

    def test_equipment_create_view_get(self):
        url = reverse("equipos_create")
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_form.html")

    def test_equipment_create_view_post_valid(self):
        url = reverse("equipos_create")
        initial_count = Equipment.objects.count()
        data = {
            "nombre": "Nuevo Equipo Gamma",
            "marca": "MarcaTest",
            "modelo": "ModeloTest",
            "serial": "SNTEST123",
            "user": self.user_client.id,
            "process": self.process.id,
            "estado_actual": EstadoEquipoChoices.EN_USO,
            "sede": "Sede Test",
            "fecha_adquisicion": date.today().strftime("%Y-%m-%d"),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302, response.content.decode())
        self.assertEqual(Equipment.objects.count(), initial_count + 1)
        new_equipment = Equipment.objects.latest("id")
        self.assertEqual(new_equipment.nombre, "Nuevo Equipo Gamma")
        self.assertEqual(new_equipment.user, self.user_client)

    def test_equipment_create_view_post_invalid(self):
        url = reverse("equipos_create")
        initial_count = Equipment.objects.count()
        data = {"marca": "SoloMarca"}
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(Equipment.objects.count(), initial_count)
        self.assertTrue(response.context["form"].errors)

    def test_equipment_update_view_get(self):
        equipment = Equipment.objects.create(
            nombre="Equipo para GET Update", user=self.user_client, process=self.process
        )
        url = reverse("equipos_update", args=[equipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_form.html")
        self.assertEqual(response.context["form"].instance, equipment)

    def test_equipment_update_view_post_valid(self):
        equipment = Equipment.objects.create(
            nombre="Equipo Original",
            serial="SNORIG",
            user=self.user_client,
            process=self.process,
        )
        url = reverse("equipos_update", args=[equipment.id])
        data = {
            "nombre": "Equipo Actualizado",
            "marca": equipment.marca or "NuevaMarca",
            "modelo": equipment.modelo or "NuevoModelo",
            "serial": "SNUPDT",
            "user": self.user_client.id,
            "process": self.process.id,
            "estado_actual": EstadoEquipoChoices.DADO_DE_BAJA,
            "sede": equipment.sede or "NuevaSede",
            "fecha_adquisicion": (equipment.fecha_adquisicion or date.today()).strftime(
                "%Y-%m-%d"
            ),
        }
        response = self.client.post(url, data)
        self.assertEqual(response.status_code, 302)
        equipment.refresh_from_db()
        self.assertEqual(equipment.nombre, "Equipo Actualizado")
        self.assertEqual(equipment.serial, "SNUPDT")
        self.assertEqual(equipment.estado_actual, EstadoEquipoChoices.DADO_DE_BAJA)

    def test_equipment_delete_view_get(self):
        equipment = Equipment.objects.create(
            nombre="Equipo para GET Delete", user=self.user_client, process=self.process
        )
        url = reverse("equipos_delete", args=[equipment.id])
        response = self.client.get(url)
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, "equipos/equipos_confirm_delete.html")

    def test_equipment_delete_view_post(self):
        equipment = Equipment.objects.create(
            nombre="Equipo para POST Delete",
            user=self.user_client,
            process=self.process,
        )
        initial_count = Equipment.objects.count()
        url = reverse("equipos_delete", args=[equipment.id])
        response = self.client.post(url)
        self.assertEqual(response.status_code, 302)
        self.assertEqual(Equipment.objects.count(), initial_count - 1)
