from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from app.models import (  # ProcessChecklistItem, # Removed this import; AsesoriaSubtypeChoices, # Removed this import; Role,; RoleChoices
    ChecklistItemDefinition,
    Process,
    ProcessStatusChoices,
    ProcessTypeChoices,
)

User = get_user_model()


class ProcessChecklistModelTests(TestCase):

    @classmethod
    def setUpTestData(cls):
        cls.test_user = User.objects.create_user(
            username="testuser_process_checklist",
            password="password123",
            email="test_pc@example.com",
        )

        # Definitions for Cálculo de Blindajes - aligned with migration 0012
        cls.def1_calc, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            name="Elaboración de cálculo.",  # Matched migration
            order=1,
            defaults={"percentage": 30},
        )
        cls.def2_calc, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            name="Elaboración de informe.",  # Matched migration
            order=2,
            defaults={"percentage": 30},
        )
        cls.def3_calc, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            name="Revisión de informe.",  # Matched migration
            order=3,
            defaults={"percentage": 20},
        )
        cls.def4_calc, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            name="Publicación de informe.",  # Matched migration
            order=4,
            defaults={"percentage": 20},
        )

        # Definitions for Control de Calidad - aligned with migration 0012
        cls.def1_ctrl, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Realización de medidas.",  # Matched migration
            order=1,
            defaults={"percentage": 30},  # Matched migration
        )
        cls.def2_ctrl, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Elaboración de informe.",  # Matched migration
            order=2,
            defaults={"percentage": 30},  # Matched migration
        )
        cls.def3_ctrl, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Revisión de informe.",  # Matched migration
            order=3,
            defaults={"percentage": 20},  # Matched migration
        )
        cls.def4_ctrl, _ = ChecklistItemDefinition.objects.get_or_create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Publicación de informe",  # Matched migration (no period here)
            order=4,
            defaults={"percentage": 20},  # Matched migration
        )

    def test_create_checklist_items_on_new_process(self):
        """Test that checklist items are created when a new process is saved."""
        process_calc = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process_calc.checklist_items.count(), 4)
        self.assertTrue(
            process_calc.checklist_items.filter(definition=self.def1_calc).exists()
        )
        self.assertTrue(
            process_calc.checklist_items.filter(definition=self.def2_calc).exists()
        )
        self.assertTrue(
            process_calc.checklist_items.filter(definition=self.def3_calc).exists()
        )
        self.assertTrue(
            process_calc.checklist_items.filter(definition=self.def4_calc).exists()
        )

        process_ctrl = Process.objects.create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(process_ctrl.checklist_items.count(), 4)  # Expect 4 items now
        self.assertTrue(
            process_ctrl.checklist_items.filter(definition=self.def1_ctrl).exists()
        )
        self.assertTrue(
            process_ctrl.checklist_items.filter(definition=self.def2_ctrl).exists()
        )
        self.assertTrue(
            process_ctrl.checklist_items.filter(definition=self.def3_ctrl).exists()
        )  # Added assertion for 3rd item
        self.assertTrue(
            process_ctrl.checklist_items.filter(definition=self.def4_ctrl).exists()
        )  # Added assertion for 4th item

    def test_get_progress_percentage(self):
        """Test calculation of progress percentage."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertEqual(
            process.get_progress_percentage(), 0, "Initial progress should be 0"
        )

        item1 = process.checklist_items.get(definition=self.def1_calc)
        item1.is_completed = True
        item1.completed_at = timezone.now()
        item1.save()
        self.assertEqual(
            process.get_progress_percentage(), 30, "Progress after completing 30% item"
        )

        item2 = process.checklist_items.get(definition=self.def2_calc)
        item2.is_completed = True
        item2.completed_at = timezone.now()
        item2.save()
        self.assertEqual(
            process.get_progress_percentage(),
            60,
            "Progress after completing another 30% item",
        )

        item3 = process.checklist_items.get(definition=self.def3_calc)
        item3.is_completed = True
        item3.completed_at = timezone.now()
        item3.save()
        self.assertEqual(
            process.get_progress_percentage(), 80, "Progress after completing 20% item"
        )

        item4 = process.checklist_items.get(definition=self.def4_calc)
        item4.is_completed = True
        item4.completed_at = timezone.now()
        item4.save()
        self.assertEqual(
            process.get_progress_percentage(),
            100,
            "Progress after completing final 20% item",
        )

    def test_reset_checklist_items_on_modification_status(self):
        """Test that checklist items are reset when status changes to EN_MODIFICACION."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        item1 = process.checklist_items.get(definition=self.def1_calc)
        item1.is_completed = True
        item1.completed_at = timezone.now()
        item1.save()

        self.assertEqual(process.get_progress_percentage(), 30)
        self.assertTrue(item1.is_completed)

        process.estado = ProcessStatusChoices.EN_MODIFICACION
        process.save(user_who_modified=self.test_user)

        item1.refresh_from_db()
        self.assertFalse(
            item1.is_completed, "Item should be marked incomplete after reset"
        )
        self.assertIsNone(item1.completed_at, "Completed_at should be None after reset")
        self.assertEqual(
            process.get_progress_percentage(), 0, "Progress should be 0 after reset"
        )

        for item in process.checklist_items.all():
            self.assertFalse(item.is_completed)
            self.assertIsNone(item.completed_at)

    def test_create_checklist_for_existing_process_without_items_on_status_change(self):
        """Test checklist creation for an old process when its status changes."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        self.assertTrue(process.checklist_items.exists())
        process.checklist_items.all().delete()  # Simulate an old process
        self.assertFalse(process.checklist_items.exists())

        process.estado = ProcessStatusChoices.EN_REVISION
        process.save(user_who_modified=self.test_user)

        self.assertEqual(
            process.checklist_items.count(), 4, "Checklist items should be recreated"
        )
        self.assertEqual(
            process.get_progress_percentage(),
            0,
            "Progress of newly created items should be 0",
        )

    def test_no_checklist_reset_if_status_not_modification(self):
        """Test that checklist items are not reset if status changes to something other than EN_MODIFICACION."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
        )
        item1 = process.checklist_items.get(definition=self.def1_calc)
        item1.is_completed = True
        item1.completed_at = timezone.now()
        item1.save()
        self.assertEqual(process.get_progress_percentage(), 30)

        process.estado = ProcessStatusChoices.EN_REVISION  # Not EN_MODIFICACION
        process.save(user_who_modified=self.test_user)

        item1.refresh_from_db()
        self.assertTrue(item1.is_completed, "Item should remain completed")
        self.assertIsNotNone(item1.completed_at, "Completed_at should remain")
        self.assertEqual(
            process.get_progress_percentage(), 30, "Progress should be preserved"
        )

    def test_process_save_with_user_who_modified_in_log(self):
        """Test that user_who_modified is correctly logged in ProcessStatusLog."""
        process = Process.objects.create(
            process_type=ProcessTypeChoices.CALCULO_BLINDAJES,
            # asesoria_subtype=AsesoriaSubtypeChoices.NO_APLICA, # Removed
            user=self.test_user,
            estado=ProcessStatusChoices.EN_PROGRESO,
            # user_who_modified is None for the creation log via Process.objects.create
        )
        creation_log = process.status_logs.latest("fecha_cambio")
        self.assertIsNone(
            creation_log.usuario_modifico,
            "user_who_modified should be None for initial creation log via create()",
        )
        self.assertEqual(creation_log.estado_nuevo, ProcessStatusChoices.EN_PROGRESO)

        process.estado = ProcessStatusChoices.EN_REVISION
        process.save(user_who_modified=self.test_user)

        self.assertEqual(process.status_logs.count(), 2)
        modification_log = process.status_logs.latest("fecha_cambio")
        self.assertEqual(
            modification_log.usuario_modifico,
            self.test_user,
            "user_who_modified should be test_user for modification log",
        )
        self.assertEqual(
            modification_log.estado_nuevo, ProcessStatusChoices.EN_REVISION
        )
        self.assertEqual(
            modification_log.estado_anterior, ProcessStatusChoices.EN_PROGRESO
        )
