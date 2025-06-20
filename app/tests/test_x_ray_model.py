import datetime

from django.contrib.auth import get_user_model
from django.test import TestCase

from app.models import Equipment, HistorialTuboRayosX

User = get_user_model()


class HistorialTuboRayosXModelTest(TestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", password="testpassword"
        )
        self.equipment = Equipment.objects.create(
            nombre="Test Equipment", user=self.user
        )

    def test_crear_historial_tubo_rayos_x(self):
        """Test creating a new X-ray tube history record."""
        historial = HistorialTuboRayosX.objects.create(
            equipment=self.equipment,
            marca="Marca Test",
            modelo="Modelo Test",
            serial="Serial Test",
            fecha_cambio=datetime.date.today(),
        )
        self.assertEqual(historial.equipment, self.equipment)
        self.assertEqual(historial.marca, "Marca Test")
        self.assertEqual(historial.modelo, "Modelo Test")
        self.assertEqual(historial.serial, "Serial Test")
        self.assertEqual(historial.fecha_cambio, datetime.date.today())
        self.assertEqual(
            str(historial),
            f"Tubo para {self.equipment.nombre} - {historial.serial} ({historial.fecha_cambio})",
        )

    def test_get_current_xray_tube(self):
        """Test the get_current_xray_tube method on the Equipment model."""
        # No tube initially
        self.assertIsNone(self.equipment.get_current_xray_tube())

        # Add a tube
        tubo1 = HistorialTuboRayosX.objects.create(
            equipment=self.equipment,
            marca="Marca 1",
            modelo="Modelo 1",
            serial="Serial 1",
            fecha_cambio=datetime.date(2024, 1, 1),
        )
        self.assertEqual(self.equipment.get_current_xray_tube(), tubo1)

        # Add a newer tube
        tubo2 = HistorialTuboRayosX.objects.create(
            equipment=self.equipment,
            marca="Marca 2",
            modelo="Modelo 2",
            serial="Serial 2",
            fecha_cambio=datetime.date(2024, 6, 1),
        )
        self.assertEqual(self.equipment.get_current_xray_tube(), tubo2)

        # Add an older tube, should not be the current one
        HistorialTuboRayosX.objects.create(
            equipment=self.equipment,
            marca="Marca 0",
            modelo="Modelo 0",
            serial="Serial 0",
            fecha_cambio=datetime.date(2023, 12, 31),
        )
        self.assertEqual(self.equipment.get_current_xray_tube(), tubo2)

    def test_historial_ordering(self):
        """Test that the history is ordered by fecha_cambio descending."""
        HistorialTuboRayosX.objects.create(
            equipment=self.equipment,
            marca="Marca 1",
            modelo="Modelo 1",
            serial="Serial 1",
            fecha_cambio=datetime.date(2024, 1, 1),
        )
        HistorialTuboRayosX.objects.create(
            equipment=self.equipment,
            marca="Marca 3",
            modelo="Modelo 3",
            serial="Serial 3",
            fecha_cambio=datetime.date(2024, 7, 1),
        )
        HistorialTuboRayosX.objects.create(
            equipment=self.equipment,
            marca="Marca 2",
            modelo="Modelo 2",
            serial="Serial 2",
            fecha_cambio=datetime.date(2024, 3, 1),
        )

        historial = self.equipment.historial_tubos_rayos_x.all()
        self.assertEqual(historial[0].serial, "Serial 3")
        self.assertEqual(historial[1].serial, "Serial 2")
        self.assertEqual(historial[2].serial, "Serial 1")
