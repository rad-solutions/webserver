import datetime  # Added for timedelta
import os
import tempfile

from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import IntegrityError
from django.test import TestCase
from django.utils import timezone  # Added for setting created_at

from ..models import Anotacion  # Add Anotacion here
from ..models import ClientProfile  # Changed from .models
from ..models import EstadoEquipoChoices  # Changed from .models
from ..models import EstadoReporteChoices  # Changed from .models
from ..models import ProcessStatusLog  # Added ProcessStatusLog
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
        self.process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.equipment = Equipment.objects.create(
            nombre="Test Equipment",
            user=self.user,  # Assuming client user owns equipment
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
                equipment=self.equipment,  # Associate with equipment
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
        self.assertEqual(
            self.report.equipment, self.equipment
        )  # Test equipment association

    def test_report_creation_without_equipment(self):
        """Test report creation without associating equipment."""
        with open(self.temp_file.name, "rb") as pdf:
            report_no_equipment = Report.objects.create(
                user=self.user,
                process=self.process,
                title="Informe Sin Equipo",
                pdf_file=SimpleUploadedFile("no_equip.pdf", pdf.read()),
            )
        self.assertIsNone(report_no_equipment.equipment)
        self.assertEqual(report_no_equipment.title, "Informe Sin Equipo")

    def test_report_string_representation(self):
        expected_string = "Report by Test: Informe de prueba"
        self.assertEqual(str(self.report), expected_string)

    def test_user_reports_relationship(self):
        self.assertEqual(self.user.reports.count(), 1)
        self.assertEqual(self.user.reports.first(), self.report)

    def test_process_reports_relationship(self):
        self.assertEqual(self.process.reports.count(), 1)
        self.assertEqual(self.process.reports.first(), self.report)

    def test_equipment_reports_relationship(self):
        """Test accessing reports from an equipment instance."""
        self.assertEqual(self.equipment.reports.count(), 1)
        self.assertEqual(self.equipment.reports.first(), self.report)

        # Create another report for the same equipment
        with open(self.temp_file.name, "rb") as pdf:
            Report.objects.create(
                user=self.user,
                title="Otro Informe para Equipo",
                pdf_file=SimpleUploadedFile("other_equip.pdf", pdf.read()),
                equipment=self.equipment,
            )
        self.assertEqual(self.equipment.reports.count(), 2)

    def test_report_equipment_set_null_on_delete(self):
        """Test that report.equipment is set to NULL when equipment is deleted."""
        equipment_to_delete = Equipment.objects.create(
            nombre="Temp Equipment", user=self.user
        )
        with open(self.temp_file.name, "rb") as pdf:
            report_with_temp_equip = Report.objects.create(
                user=self.user,
                title="Informe con Equipo Temporal",
                pdf_file=SimpleUploadedFile("temp_equip_report.pdf", pdf.read()),
                equipment=equipment_to_delete,
            )
        self.assertEqual(report_with_temp_equip.equipment, equipment_to_delete)

        equipment_to_delete.delete()
        report_with_temp_equip.refresh_from_db()
        self.assertIsNone(report_with_temp_equip.equipment)

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
        self.another_user = User.objects.create_user(
            username="anotherprocuser", password="password"
        )  # For testing user_who_modified

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

        # Test that a ProcessStatusLog entry is created for a new process
        self.assertEqual(ProcessStatusLog.objects.count(), 1)
        log_entry = ProcessStatusLog.objects.first()
        self.assertEqual(log_entry.proceso, process)
        self.assertIsNone(log_entry.estado_anterior)
        self.assertEqual(log_entry.estado_nuevo, ProcessStatusChoices.EN_PROGRESO)
        self.assertIsNone(
            log_entry.usuario_modifico
        )  # No user_who_modified passed on initial create

    def test_process_creation_with_user_who_modified(self):
        """Test process creation logs status with user_who_modified when saving a new instance."""
        ProcessStatusLog.objects.all().delete()  # Ensure a clean slate for log counting

        process_new = Process(
            user=self.user,
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        # Call save() on a new, unsaved instance, passing user_who_modified
        process_new.save(user_who_modified=self.another_user)

        self.assertEqual(
            ProcessStatusLog.objects.count(),
            1,
            "A log entry should be created for a new process.",
        )
        log_entry_new = ProcessStatusLog.objects.first()
        self.assertIsNotNone(log_entry_new, "Log entry should exist.")
        self.assertEqual(log_entry_new.proceso, process_new)
        self.assertIsNone(
            log_entry_new.estado_anterior,
            "estado_anterior should be None for a new process log.",
        )
        self.assertEqual(log_entry_new.estado_nuevo, ProcessStatusChoices.EN_PROGRESO)
        self.assertEqual(
            log_entry_new.usuario_modifico,
            self.another_user,
            "usuario_modifico should be correctly logged.",
        )

    def test_process_status_change_logs_entry(self):
        """Test that changing a process's status creates a log entry."""
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        # Initial creation log
        self.assertEqual(ProcessStatusLog.objects.count(), 1)
        initial_log = ProcessStatusLog.objects.first()

        # Change status
        process.estado = ProcessStatusChoices.EN_REVISION
        process.save(user_who_modified=self.another_user)

        self.assertEqual(ProcessStatusLog.objects.count(), 2)
        change_log = ProcessStatusLog.objects.exclude(pk=initial_log.pk).first()

        self.assertIsNotNone(change_log)
        self.assertEqual(change_log.proceso, process)
        self.assertEqual(change_log.estado_anterior, ProcessStatusChoices.EN_PROGRESO)
        self.assertEqual(change_log.estado_nuevo, ProcessStatusChoices.EN_REVISION)
        self.assertEqual(change_log.usuario_modifico, self.another_user)

    def test_process_save_no_status_change_no_new_log(self):
        """Test that saving a process without changing status does not create a new log."""
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(ProcessStatusLog.objects.count(), 1)  # Initial log

        # Save again without changing status
        process.save()
        self.assertEqual(ProcessStatusLog.objects.count(), 1)  # Should still be 1

        process.save(user_who_modified=self.another_user)  # Even with user
        self.assertEqual(ProcessStatusLog.objects.count(), 1)

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
        # Process for general use, not necessarily for QC
        self.general_process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        # Process specifically for Quality Control
        self.qc_process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        # Dummy PDF file for reports
        self.dummy_pdf = SimpleUploadedFile(
            "dummy.pdf", b"pdf_content", content_type="application/pdf"
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

    def test_get_last_quality_control_report_no_reports(self):
        """Return None when no reports are linked to the equipment."""
        equipment = Equipment.objects.create(
            nombre="Equipo Sin Informes", user=self.user
        )
        self.assertIsNone(equipment.get_last_quality_control_report())

    def test_get_last_quality_control_report_only_non_qc_reports(self):
        """Return None when only non-QC reports are linked."""
        equipment = Equipment.objects.create(nombre="Equipo Solo NoQC", user=self.user)
        Report.objects.create(
            user=self.user,
            process=self.general_process,
            equipment=equipment,
            title="Informe NoQC",
            pdf_file=self.dummy_pdf,
        )
        self.assertIsNone(equipment.get_last_quality_control_report())

    def test_get_last_quality_control_report_no_qc_reports(self):
        """Return None when there are non-QC but no QC reports linked."""
        equipment = Equipment.objects.create(
            nombre="Equipo NoQC Informes", user=self.user
        )
        Report.objects.create(
            user=self.user,
            process=self.general_process,
            equipment=equipment,
            title="Informe Asesoria",
            pdf_file=self.dummy_pdf,
        )
        self.assertIsNone(equipment.get_last_quality_control_report())

    def test_get_last_quality_control_report_one_qc_report(self):
        """Return the single QC report linked to the equipment."""
        equipment = Equipment.objects.create(
            nombre="Equipo Con Informe QC", user=self.user
        )
        report = Report.objects.create(
            user=self.user,
            process=self.qc_process,
            equipment=equipment,
            title="Informe QC",
            pdf_file=self.dummy_pdf,
        )
        self.assertEqual(equipment.get_last_quality_control_report(), report)

    def test_get_last_quality_control_report_multiple_qc_reports(self):
        """Return the newest QC report among multiple linked to the equipment."""
        equipment = Equipment.objects.create(nombre="Equipo Varios QC", user=self.user)
        old = Report.objects.create(
            user=self.user,
            process=self.qc_process,
            equipment=equipment,
            title="QC Antiguo",
            pdf_file=self.dummy_pdf,
        )
        Report.objects.filter(pk=old.pk).update(
            created_at=timezone.now() - datetime.timedelta(days=2)
        )
        new = Report.objects.create(
            user=self.user,
            process=self.qc_process,
            equipment=equipment,
            title="QC Reciente",
            pdf_file=self.dummy_pdf,
            created_at=timezone.now(),
        )
        self.assertEqual(equipment.get_last_quality_control_report(), new)

    def test_get_quality_control_history_no_reports(self):
        """Return empty queryset when no reports are linked to the equipment."""
        equipment = Equipment.objects.create(
            nombre="Equipo Sin Historial", user=self.user
        )
        self.assertQuerySetEqual(equipment.get_quality_control_history(), [])

    def test_get_quality_control_history_only_non_qc_reports(self):
        """Return empty queryset when only non-QC reports are linked."""
        equipment = Equipment.objects.create(
            nombre="Equipo Historial NoQC", user=self.user
        )
        Report.objects.create(
            user=self.user,
            process=self.general_process,
            equipment=equipment,
            title="Informe NoQC",
            pdf_file=self.dummy_pdf,
        )
        self.assertQuerySetEqual(equipment.get_quality_control_history(), [])

    def test_get_quality_control_history_no_qc_reports(self):
        """Return empty queryset when there are no QC reports linked."""
        equipment = Equipment.objects.create(
            nombre="Equipo NoQC Historial", user=self.user
        )
        Report.objects.create(
            user=self.user,
            process=self.general_process,
            equipment=equipment,
            title="Informe Asesoria",
            pdf_file=self.dummy_pdf,
        )
        self.assertQuerySetEqual(equipment.get_quality_control_history(), [])

    def test_get_quality_control_history_one_qc_report(self):
        """Return queryset with the single QC report linked."""
        equipment = Equipment.objects.create(
            nombre="Equipo Historial Un Informe QC", user=self.user
        )
        report = Report.objects.create(
            user=self.user,
            process=self.qc_process,
            equipment=equipment,
            title="Informe QC Hist",
            pdf_file=self.dummy_pdf,
        )
        history = equipment.get_quality_control_history()
        self.assertEqual(history.count(), 1)
        self.assertEqual(history.first(), report)

    def test_get_quality_control_history_multiple_qc_reports(self):
        """Return all QC reports linked, ordered by creation date."""
        equipment = Equipment.objects.create(
            nombre="Equipo Historial Varios QC", user=self.user
        )
        r1 = Report.objects.create(
            user=self.user,
            process=self.qc_process,
            equipment=equipment,
            title="Antiguo",
            pdf_file=self.dummy_pdf,
        )
        Report.objects.filter(pk=r1.pk).update(
            created_at=timezone.now() - datetime.timedelta(days=3)
        )
        r1.refresh_from_db()
        r2 = Report.objects.create(
            user=self.user,
            process=self.qc_process,
            equipment=equipment,
            title="Medio",
            pdf_file=self.dummy_pdf,
        )
        Report.objects.filter(pk=r2.pk).update(
            created_at=timezone.now() - datetime.timedelta(days=2)
        )
        r2.refresh_from_db()
        r3 = Report.objects.create(
            user=self.user,
            process=self.qc_process,
            equipment=equipment,
            title="Reciente",
            pdf_file=self.dummy_pdf,
            created_at=timezone.now() - datetime.timedelta(days=1),
        )
        r3.refresh_from_db()
        history = equipment.get_quality_control_history()
        self.assertEqual(history.count(), 3)
        self.assertEqual(list(history), [r1, r2, r3])


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


class AnotacionModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(
            username="testuser1",
            email="test1@example.com",
            password="testpassword1",
            first_name="Test1",
            last_name="User1",
        )
        self.user2 = User.objects.create_user(
            username="testuser2",
            email="test2@example.com",
            password="testpassword2",
            first_name="Test2",
            last_name="User2",
        )
        self.process = Process.objects.create(
            user=self.user1,  # Assuming a process needs a user
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )

    def test_anotacion_creation(self):
        """Test that an anotacion can be created successfully."""
        anotacion = Anotacion.objects.create(
            proceso=self.process,
            usuario=self.user1,
            contenido="Esta es una anotación de prueba.",
        )
        self.assertEqual(Anotacion.objects.count(), 1)
        self.assertEqual(anotacion.proceso, self.process)
        self.assertEqual(anotacion.usuario, self.user1)
        self.assertEqual(anotacion.contenido, "Esta es una anotación de prueba.")
        self.assertIsNotNone(anotacion.fecha_creacion)

    def test_anotacion_string_representation(self):
        """Test the string representation of an anotacion."""
        anotacion = Anotacion.objects.create(
            proceso=self.process,
            usuario=self.user1,
            contenido="Contenido para str.",
        )
        expected_str = f"Anotación para {self.process.get_process_type_display()} ({self.process.id}) por {self.user1.username} el {anotacion.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(anotacion), expected_str)

    def test_anotacion_string_representation_no_user(self):
        """Test the string representation when usuario is None."""
        anotacion = Anotacion.objects.create(
            proceso=self.process, usuario=None, contenido="Sistema generó esta nota."
        )
        expected_str = f"Anotación para {self.process.get_process_type_display()} ({self.process.id}) por Sistema el {anotacion.fecha_creacion.strftime('%Y-%m-%d %H:%M')}"
        self.assertEqual(str(anotacion), expected_str)

    def test_anotacion_ordering(self):
        """Test that anotaciones are ordered by fecha_creacion descending."""
        anotacion1 = Anotacion.objects.create(
            proceso=self.process,
            usuario=self.user1,
            contenido="Anotación antigua.",
            fecha_creacion=timezone.now() - datetime.timedelta(days=1),
        )
        anotacion2 = Anotacion.objects.create(
            proceso=self.process,
            usuario=self.user1,
            contenido="Anotación más reciente.",
            fecha_creacion=timezone.now(),
        )
        anotacion3 = Anotacion.objects.create(
            proceso=self.process,
            usuario=self.user2,
            contenido="Anotación intermedia.",
            fecha_creacion=timezone.now() - datetime.timedelta(hours=12),
        )

        # Manually set dates to ensure order for testing, as auto_now_add might be too close
        Anotacion.objects.filter(pk=anotacion1.pk).update(
            fecha_creacion=timezone.now() - datetime.timedelta(days=1)
        )
        Anotacion.objects.filter(pk=anotacion2.pk).update(fecha_creacion=timezone.now())
        Anotacion.objects.filter(pk=anotacion3.pk).update(
            fecha_creacion=timezone.now() - datetime.timedelta(hours=12)
        )

        # Re-fetch to get updated timestamps
        anotacion1.refresh_from_db()
        anotacion2.refresh_from_db()
        anotacion3.refresh_from_db()

        anotaciones = list(Anotacion.objects.filter(proceso=self.process))
        self.assertEqual(anotaciones, [anotacion2, anotacion3, anotacion1])

    def test_related_name_from_process(self):
        """Test accessing anotaciones from a process instance."""
        Anotacion.objects.create(
            proceso=self.process, usuario=self.user1, contenido="Nota 1"
        )
        Anotacion.objects.create(
            proceso=self.process, usuario=self.user2, contenido="Nota 2"
        )
        self.assertEqual(self.process.anotaciones.count(), 2)

    def test_related_name_from_user(self):
        """Test accessing anotaciones_creadas from a user instance."""
        Anotacion.objects.create(
            proceso=self.process, usuario=self.user1, contenido="Nota de User1"
        )
        another_process = Process.objects.create(
            user=self.user2,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            estado=ProcessStatusChoices.FINALIZADO,
        )
        Anotacion.objects.create(
            proceso=another_process, usuario=self.user1, contenido="Otra nota de User1"
        )
        self.assertEqual(self.user1.anotaciones_creadas.count(), 2)
        self.assertEqual(self.user2.anotaciones_creadas.count(), 0)

    def test_anotacion_without_user(self):
        """Test creating an anotacion with a null user."""
        anotacion = Anotacion.objects.create(
            proceso=self.process, usuario=None, contenido="Anotación del sistema."
        )
        self.assertIsNone(anotacion.usuario)
        self.assertEqual(Anotacion.objects.count(), 1)

    def test_cascade_delete_with_process(self):
        """Test that anotaciones are deleted when their process is deleted."""
        Anotacion.objects.create(
            proceso=self.process, usuario=self.user1, contenido="Contenido"
        )
        self.assertEqual(Anotacion.objects.count(), 1)
        self.process.delete()
        self.assertEqual(Anotacion.objects.count(), 0)

    def test_set_null_on_user_delete(self):
        """Test that anotacion.usuario is set to NULL when the user is deleted."""
        # Create a process associated with user2, so it doesn't get deleted
        # when user1 (the anotacion's author) is deleted.
        process_for_this_test = Process.objects.create(
            user=self.user2,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        anotacion = Anotacion.objects.create(
            proceso=process_for_this_test,  # Use the process linked to user2
            usuario=self.user1,  # user1 is the author we will delete
            contenido="Contenido",
        )
        self.assertEqual(anotacion.usuario, self.user1)

        # Ensure the anotacion exists before user deletion
        self.assertTrue(Anotacion.objects.filter(pk=anotacion.pk).exists())

        self.user1.delete()  # Delete user1 (the author)

        # The anotacion itself should still exist
        self.assertTrue(
            Anotacion.objects.filter(pk=anotacion.pk).exists(),
            "Anotacion should still exist after its author is deleted.",
        )

        anotacion.refresh_from_db()  # This should now work
        self.assertIsNone(
            anotacion.usuario, "Anotacion.usuario should be None after author deletion."
        )

        # Verify the specific anotacion we are testing still exists and its user is null
        self.assertTrue(
            Anotacion.objects.filter(pk=anotacion.pk, usuario__isnull=True).exists()
        )


class ProcessStatusLogModelTest(TestCase):
    def setUp(self):
        self.user1 = User.objects.create_user(username="loguser1", password="password")
        self.user2 = User.objects.create_user(username="loguser2", password="password")
        # Create self.process WITHOUT it automatically creating a log entry here,
        # so that test methods have full control over log creation for self.process.
        # Or, be mindful that self.process.save() in Process.objects.create() WILL create a log.
        # For clarity, let's allow it to create its initial log.
        self.process = Process.objects.create(
            user=self.user1,
            process_type=ProcessTypeChoices.ASESORIA,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        # At this point, one log exists for self.process due to its creation.

    def test_process_status_log_creation(self):
        """Test basic creation of a ProcessStatusLog entry."""
        # One log already exists from self.process creation in setUp.
        initial_log_count = ProcessStatusLog.objects.count()

        log_entry = ProcessStatusLog.objects.create(
            proceso=self.process,
            estado_anterior=ProcessStatusChoices.EN_PROGRESO,
            estado_nuevo=ProcessStatusChoices.EN_REVISION,
            usuario_modifico=self.user2,
        )
        self.assertEqual(log_entry.proceso, self.process)
        self.assertEqual(log_entry.estado_anterior, ProcessStatusChoices.EN_PROGRESO)
        self.assertEqual(log_entry.estado_nuevo, ProcessStatusChoices.EN_REVISION)
        self.assertEqual(log_entry.usuario_modifico, self.user2)
        self.assertIsNotNone(log_entry.fecha_cambio)
        # Check that a new log was added to the existing ones.
        self.assertEqual(ProcessStatusLog.objects.count(), initial_log_count + 1)

    def test_process_status_log_creation_no_anterior_no_user(self):
        """Test log creation with no anterior_estado and no usuario_modifico."""
        log_entry = ProcessStatusLog.objects.create(
            proceso=self.process,
            estado_nuevo=ProcessStatusChoices.RADICADO,
            # usuario_modifico=None implicitly
        )
        self.assertIsNone(log_entry.estado_anterior)
        self.assertIsNone(log_entry.usuario_modifico)
        self.assertEqual(log_entry.estado_nuevo, ProcessStatusChoices.RADICADO)

    def test_process_status_log_string_representation(self):
        """Test the string representation of the log entry."""
        log_entry = ProcessStatusLog.objects.create(
            proceso=self.process,
            estado_anterior=ProcessStatusChoices.EN_PROGRESO,
            estado_nuevo=ProcessStatusChoices.EN_REVISION,
            usuario_modifico=self.user2,
        )
        expected_str_part_proceso = (
            f"{self.process.get_process_type_display()} ({self.process.id})"
        )
        expected_str = (
            f"Proceso {expected_str_part_proceso}: {ProcessStatusChoices.EN_PROGRESO.label} -> "
            f"{ProcessStatusChoices.EN_REVISION.label} por {self.user2.username} el "
            f"{log_entry.fecha_cambio.strftime('%Y-%m-%d %H:%M')}"
        )
        self.assertEqual(str(log_entry), expected_str)

    def test_process_status_log_string_representation_no_user_no_anterior(self):
        """Test string representation with no user and no anterior estado."""
        # One log from setUp.
        initial_log_count = ProcessStatusLog.objects.count()
        log_entry = ProcessStatusLog.objects.create(
            proceso=self.process,
            estado_nuevo=ProcessStatusChoices.FINALIZADO,
            # usuario_modifico=None implicitly
        )
        expected_str_part_proceso = (
            f"{self.process.get_process_type_display()} ({self.process.id})"
        )
        expected_str = (
            f"Proceso {expected_str_part_proceso}: N/A -> "
            f"{ProcessStatusChoices.FINALIZADO.label} por Sistema el "
            f"{log_entry.fecha_cambio.strftime('%Y-%m-%d %H:%M')}"
        )
        self.assertEqual(str(log_entry), expected_str)
        self.assertEqual(
            ProcessStatusLog.objects.count(), initial_log_count + 1
        )  # Ensure test isolation for count

    def test_process_status_log_ordering(self):
        """Test that logs are ordered by fecha_cambio descending."""
        # Clear any logs for self.process created in setUp to ensure a clean test.
        ProcessStatusLog.objects.filter(proceso=self.process).delete()

        time_now = timezone.now()

        # Create logs with controlled timestamps
        log1_time = time_now - datetime.timedelta(days=2)  # Oldest
        log2_time = time_now - datetime.timedelta(days=1)  # Middle
        log3_time = time_now  # Newest

        # Create in an order different from their timestamps to test sorting
        log2 = ProcessStatusLog.objects.create(
            proceso=self.process, estado_nuevo=ProcessStatusChoices.EN_REVISION
        )
        ProcessStatusLog.objects.filter(pk=log2.pk).update(fecha_cambio=log2_time)
        log2.refresh_from_db()

        log1 = ProcessStatusLog.objects.create(
            proceso=self.process, estado_nuevo=ProcessStatusChoices.EN_PROGRESO
        )
        ProcessStatusLog.objects.filter(pk=log1.pk).update(fecha_cambio=log1_time)
        log1.refresh_from_db()

        log3 = ProcessStatusLog.objects.create(
            proceso=self.process, estado_nuevo=ProcessStatusChoices.RADICADO
        )
        ProcessStatusLog.objects.filter(pk=log3.pk).update(
            fecha_cambio=log3_time
        )  # Ensure it's set if auto_add_now has variance
        log3.refresh_from_db()

        logs_for_process = ProcessStatusLog.objects.filter(proceso=self.process)

        # Expected order: newest (log3), middle (log2), oldest (log1)
        self.assertEqual(list(logs_for_process), [log3, log2, log1])

    def test_cascade_delete_with_process(self):
        """Test that logs are deleted when the associated process is deleted."""
        # self.process has one log from setUp.
        # Create an additional log entry for this process to ensure multiple are deleted.
        ProcessStatusLog.objects.create(
            proceso=self.process,
            estado_anterior=ProcessStatusChoices.EN_PROGRESO,
            estado_nuevo=ProcessStatusChoices.EN_REVISION,
            usuario_modifico=self.user2,
        )
        # Now self.process should have 2 logs.
        self.assertEqual(
            self.process.status_logs.count(),
            2,
            "Process should have 2 logs before deletion.",
        )

        process_pk = self.process.pk  # Store pk for querying after delete
        self.process.delete()

        # Verify no logs exist for the deleted process_pk
        self.assertFalse(
            ProcessStatusLog.objects.filter(proceso_id=process_pk).exists(),
            "Logs for the deleted process should also be deleted.",
        )

    def test_set_null_on_user_delete(self):
        """Test that usuario_modifico is set to NULL when the user is deleted."""
        user_to_delete = User.objects.create_user(
            username="deletelogger", password="pass"
        )
        log_entry = ProcessStatusLog.objects.create(
            proceso=self.process,
            estado_nuevo=ProcessStatusChoices.EN_PROGRESO,
            usuario_modifico=user_to_delete,
        )
        self.assertEqual(log_entry.usuario_modifico, user_to_delete)
        user_to_delete.delete()
        log_entry.refresh_from_db()
        self.assertIsNone(log_entry.usuario_modifico)
        self.assertTrue(ProcessStatusLog.objects.filter(pk=log_entry.pk).exists())
