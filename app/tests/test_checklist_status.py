from django.contrib.auth import get_user_model
from django.test import TestCase

from app.models import (
    ChecklistItemDefinition,
    ChecklistItemStatusChoices,
    ChecklistItemStatusLog,
    Process,
    ProcessChecklistItem,
    ProcessTypeChoices,
    Role,
    RoleChoices,
)


class ChecklistItemStatusTest(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            username="testuser", password="testpassword"
        )
        self.staff_user = get_user_model().objects.create_user(
            username="staffuser", password="testpassword", is_staff=True
        )
        # Create roles if they don't exist
        Role.objects.get_or_create(name=RoleChoices.DIRECTOR_TECNICO)

        self.process = Process.objects.create(
            user=self.user, process_type=ProcessTypeChoices.CONTROL_CALIDAD
        )
        self.definition = ChecklistItemDefinition.objects.create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Test Item",
            order=1,
            percentage=50,
        )
        self.checklist_item = ProcessChecklistItem.objects.create(
            process=self.process, definition=self.definition
        )

    def test_checklist_item_initial_status(self):
        """Test that a new checklist item has 'Pendiente' as initial status."""
        self.assertEqual(
            self.checklist_item.status, ChecklistItemStatusChoices.PENDIENTE
        )
        self.assertFalse(self.checklist_item.is_completed)

    def test_checklist_item_status_change_creates_log(self):
        """Test that changing the status of a checklist item creates a log entry."""
        initial_log_count = ChecklistItemStatusLog.objects.count()

        self.checklist_item.status = ChecklistItemStatusChoices.EN_PROGRESO
        self.checklist_item.save(user_who_modified=self.staff_user)

        self.assertEqual(ChecklistItemStatusLog.objects.count(), initial_log_count + 1)
        log_entry = ChecklistItemStatusLog.objects.latest("fecha_cambio")
        self.assertEqual(log_entry.item, self.checklist_item)
        self.assertEqual(
            log_entry.estado_anterior, ChecklistItemStatusChoices.PENDIENTE
        )
        self.assertEqual(log_entry.estado_nuevo, ChecklistItemStatusChoices.EN_PROGRESO)
        self.assertEqual(log_entry.usuario_modifico, self.staff_user)

    def test_is_completed_updates_with_status(self):
        """Test that is_completed property is updated when status changes to 'Aprobado'."""
        self.assertFalse(self.checklist_item.is_completed)
        self.checklist_item.status = ChecklistItemStatusChoices.APROBADO
        self.checklist_item.save()
        self.assertTrue(self.checklist_item.is_completed)

        self.checklist_item.status = ChecklistItemStatusChoices.EN_REVISION
        self.checklist_item.save()
        self.assertFalse(self.checklist_item.is_completed)

    def test_get_progress_percentage(self):
        """Test that the process progress percentage is calculated correctly based on 'Aprobado' status."""
        self.assertEqual(self.process.get_progress_percentage(), 0)

        definition2 = ChecklistItemDefinition.objects.create(
            process_type=ProcessTypeChoices.CONTROL_CALIDAD,
            name="Test Item 2",
            order=2,
            percentage=50,
        )
        item2 = ProcessChecklistItem.objects.create(
            process=self.process, definition=definition2
        )

        self.checklist_item.status = ChecklistItemStatusChoices.APROBADO
        self.checklist_item.save()

        self.assertEqual(self.process.get_progress_percentage(), 50)

        item2.status = ChecklistItemStatusChoices.APROBADO
        item2.save()

        self.assertEqual(self.process.get_progress_percentage(), 100)

    def test_reset_checklist_items(self):
        """Test that resetting checklist items sets status to 'Pendiente'."""
        self.checklist_item.status = ChecklistItemStatusChoices.APROBADO
        self.checklist_item.save()
        self.assertTrue(self.checklist_item.is_completed)

        self.process._reset_checklist_items()

        self.checklist_item.refresh_from_db()
        self.assertEqual(
            self.checklist_item.status, ChecklistItemStatusChoices.PENDIENTE
        )
        self.assertFalse(self.checklist_item.is_completed)
        self.assertIsNone(self.checklist_item.completed_at)
        self.assertIsNone(self.checklist_item.completed_by)
