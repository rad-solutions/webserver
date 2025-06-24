from django.test import TestCase

from app.models import (
    Equipment,
    PracticeCategoryChoices,
    Process,
    ProcessTypeChoices,
    User,
)


class EquipmentModelTest(TestCase):
    def setUp(self):
        """Set up basic data for tests."""
        self.user = User.objects.create_user(
            username="testclient", password="password123"
        )

    def test_get_report_title_default_quality_control(self):
        """Test that the default report title is 'Informes de Control de Calidad'.

        This is for a standard process.
        """
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            practice_category=PracticeCategoryChoices.MEDICA_CAT1,
        )
        equipment = Equipment.objects.create(
            nombre="Equipo Rayos X", user=self.user, process=process
        )
        # We use str() to resolve the lazy translation proxy
        self.assertEqual(
            str(equipment.get_report_title()), "Informes de Control de Calidad"
        )

    def test_get_report_title_environmental_study_veterinaria(self):
        """Test that the report title is 'Informes de Estudio Ambiental'.

        This is for the 'Veterinaria' practice category.
        """
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            practice_category=PracticeCategoryChoices.VETERINARIA,
        )
        equipment = Equipment.objects.create(
            nombre="Equipo Vet", user=self.user, process=process
        )
        self.assertEqual(
            str(equipment.get_report_title()), "Informes de Estudio Ambiental"
        )

    def test_get_report_title_environmental_study_industrial(self):
        """Test that the report title is 'Informes de Estudio Ambiental'.

        This is for the 'Industrial' practice category.
        """
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            practice_category=PracticeCategoryChoices.INDUSTRIAL,
        )
        equipment = Equipment.objects.create(
            nombre="Equipo Industrial", user=self.user, process=process
        )
        self.assertEqual(
            str(equipment.get_report_title()), "Informes de Estudio Ambiental"
        )

    def test_get_report_title_environmental_study_investigacion(self):
        """Test that the report title is 'Informes de Estudio Ambiental'.

        This is for the 'Investigación' practice category.
        """
        process = Process.objects.create(
            user=self.user,
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            practice_category=PracticeCategoryChoices.INVESTIGACION,
        )
        equipment = Equipment.objects.create(
            nombre="Equipo de Investigación", user=self.user, process=process
        )
        self.assertEqual(
            str(equipment.get_report_title()), "Informes de Estudio Ambiental"
        )

    def test_get_report_title_no_process(self):
        """Test that the report title defaults to 'Informes de Control de Calidad'.

        This is for when the equipment is not linked to a process.
        """
        equipment = Equipment.objects.create(
            nombre="Equipo Sin Proceso", user=self.user
        )
        self.assertEqual(
            str(equipment.get_report_title()), "Informes de Control de Calidad"
        )
