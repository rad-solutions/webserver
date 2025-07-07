import os

from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import TestCase

from app.models import Anotacion, Process, ProcessTypeChoices, Report, Role

User = get_user_model()


class ReportHistoryTests(TestCase):
    def setUp(self):
        # Create roles
        self.client_role = Role.objects.create(name="cliente")
        self.tech_role = Role.objects.create(name="personal_tecnico_apoyo")

        # Create users
        self.client_user = User.objects.create_user(
            username="client",
            password="password",
            first_name="Client",
            last_name="User",
        )
        self.client_user.roles.add(self.client_role)

        self.tech_user = User.objects.create_user(
            username="tech", password="password", first_name="Tech", last_name="User"
        )
        self.tech_user.roles.add(self.tech_role)

        # Create a process
        self.process = Process.objects.create(
            user=self.client_user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
        )

        # Create a report without a file
        self.report = Report.objects.create(
            user=self.client_user,
            process=self.process,
            title="Initial Report",
        )

        # Mock files
        self.file1 = SimpleUploadedFile(
            "file1.pdf", b"file_content_1", content_type="application/pdf"
        )
        self.file2 = SimpleUploadedFile(
            "file2.pdf", b"file_content_2", content_type="application/pdf"
        )

    def tearDown(self):
        for report in Report.objects.all():
            if report.pdf_file and hasattr(report.pdf_file, "path"):
                if os.path.exists(report.pdf_file.path):
                    try:
                        os.remove(report.pdf_file.path)
                    except OSError:
                        pass

    def test_anotacion_created_on_file_addition(self):
        """Test that an anotacion is created when a file is first added."""
        self.report.pdf_file = self.file1
        self.report.save(user_who_modified=self.tech_user)

        self.assertEqual(Anotacion.objects.count(), 1)
        anotacion = Anotacion.objects.first()
        self.assertEqual(anotacion.proceso, self.process)
        self.assertEqual(anotacion.usuario, self.tech_user)
        self.assertIn("Se agregó el archivo", anotacion.contenido)
        self.assertIn("file1", anotacion.contenido)

    def test_anotacion_created_on_file_update(self):
        """Test that an anotacion is created when the file is changed."""
        # First, add a file
        self.report.pdf_file = self.file1
        self.report.save(user_who_modified=self.tech_user)

        # Now, update the file
        self.report.pdf_file = self.file2
        self.report.save(user_who_modified=self.tech_user)

        self.assertEqual(Anotacion.objects.count(), 2)
        anotacion = Anotacion.objects.latest("fecha_creacion")
        self.assertEqual(anotacion.proceso, self.process)
        self.assertEqual(anotacion.usuario, self.tech_user)
        self.assertIn("Se actualizó el archivo", anotacion.contenido)
        self.assertIn("file2.pdf", anotacion.contenido)

    def test_anotacion_created_on_file_removal(self):
        """Test that an anotacion is created when the file is removed."""
        # Add a file first
        self.report.pdf_file = self.file1
        self.report.save(user_who_modified=self.tech_user)

        # Now remove the file
        self.report.pdf_file = None
        self.report.save(user_who_modified=self.tech_user)

        self.assertEqual(Anotacion.objects.count(), 2)
        anotacion = Anotacion.objects.latest("fecha_creacion")
        self.assertEqual(anotacion.proceso, self.process)
        self.assertEqual(anotacion.usuario, self.tech_user)
        self.assertIn("Se eliminó el archivo", anotacion.contenido)

    def test_no_anotacion_if_file_not_changed(self):
        """Test that no anotacion is created if the file is not changed."""
        self.report.title = "Updated Title"
        self.report.save(user_who_modified=self.tech_user)
        self.assertEqual(Anotacion.objects.count(), 0)

    def test_no_anotacion_on_report_creation(self):
        """Test that no anotacion is created when the report is first created (even with a file)."""
        Anotacion.objects.all().delete()  # Clear any anotaciones from setUp

        Report.objects.create(
            user=self.client_user,
            process=self.process,
            title="New Report with File",
            pdf_file=self.file1,
        )
        self.assertEqual(Anotacion.objects.count(), 0)
