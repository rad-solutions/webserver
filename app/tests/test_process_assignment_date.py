from django.contrib.auth import get_user_model
from django.test import TestCase
from django.utils import timezone

from app.models import Process, Role, RoleChoices

User = get_user_model()


class ProcessAssignmentDateTest(TestCase):
    def setUp(self):
        """Set up base data for tests."""
        # Create user roles
        self.role_gerente = Role.objects.create(name=RoleChoices.GERENTE)
        self.role_tecnico = Role.objects.create(name=RoleChoices.PERSONAL_TECNICO_APOYO)

        # Create a client user
        self.client_user = User.objects.create_user(
            username="testclient", password="password123"
        )

        # Create internal users
        self.internal_user_1 = User.objects.create_user(
            username="internal1", password="password123"
        )
        self.internal_user_1.roles.add(self.role_gerente)

        self.internal_user_2 = User.objects.create_user(
            username="internal2", password="password123"
        )
        self.internal_user_2.roles.add(self.role_tecnico)

        # Create a process
        self.process = Process.objects.create(user=self.client_user)

    def test_assignment_date_set_on_first_assignment(self):
        """Test that fecha_asignacion is set when a user is first assigned."""
        self.assertIsNone(self.process.fecha_asignacion)

        # Assign a user for the first time
        self.process.assigned_to.add(self.internal_user_1)

        # Refresh the instance from the database to get the updated field
        self.process.refresh_from_db()

        self.assertIsNotNone(self.process.fecha_asignacion)
        self.assertTrue(isinstance(self.process.fecha_asignacion, timezone.datetime))

    def test_assignment_date_not_changed_on_subsequent_assignment(self):
        """Test that fecha_asignacion does not change on subsequent assignments."""
        # First assignment
        self.process.assigned_to.add(self.internal_user_1)
        self.process.refresh_from_db()

        first_assignment_date = self.process.fecha_asignacion
        self.assertIsNotNone(first_assignment_date)

        # Make some time pass
        # In a real scenario, you might need to mock timezone.now() to simulate time passing
        # but for this check, just adding another user is sufficient.

        # Second assignment
        self.process.assigned_to.add(self.internal_user_2)
        self.process.refresh_from_db()

        # Verify the assignment date has not changed
        self.assertEqual(self.process.fecha_asignacion, first_assignment_date)

    def test_assignment_date_remains_none_if_not_assigned(self):
        """Test that fecha_asignacion remains None if the process is saved without assignments."""
        # The process is created in setUp() without assignments
        self.assertIsNone(self.process.fecha_asignacion)

        # Save the process again without making assignments
        self.process.save()
        self.process.refresh_from_db()

        self.assertIsNone(self.process.fecha_asignacion)
