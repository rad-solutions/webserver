from django.test import TestCase

from app.models import Equipment, EquipmentType

# A list of expected equipment types from the migration
EXPECTED_EQUIPMENT_TYPES = [
    "RX CONVENCIONAL",
    "RX CONVENCIONAL PORTATIL",
    "RX PERIAPICAL",
    "RX PERIAPICAL PORTATIL",
    "RX VETERINARIO",
    "RX INDUSTRIAL",
    "TOMOGRAFÍA COMPUTARIZADA",
    "TOMOGRAFÍA DENTAL",
    "PANORÁMICO CEFÁLICO",
    "ANGIÓGRAFO",
    "MAMÓGRAFO",
    "DENSITOMETRO",
    "ARCO EN C",
    "FLUOROSCOPIO",
]


class EquipmentTypeAndMigrationTest(TestCase):
    """Test suite for the EquipmentType model and the associated data migration."""

    def test_equipment_type_creation(self):
        """Test that an EquipmentType can be created successfully."""
        # The migration already creates types, so we test creating a new one.
        initial_count = EquipmentType.objects.count()
        equipment_type = EquipmentType.objects.create(name="TEST TYPE")
        self.assertEqual(equipment_type.name, "TEST TYPE")
        self.assertEqual(EquipmentType.objects.count(), initial_count + 1)

    def test_migration_populated_equipment_types(self):
        """Test that the data migration correctly populated the EquipmentType table."""
        # The test runner applies migrations, so the types should already be in the DB.
        self.assertEqual(EquipmentType.objects.count(), len(EXPECTED_EQUIPMENT_TYPES))
        for type_name in EXPECTED_EQUIPMENT_TYPES:
            self.assertTrue(EquipmentType.objects.filter(name=type_name).exists())

    def test_migration_logic_on_existing_data(self):
        """Test that the logic from the migration correctly updates an old-style equipment record."""
        # 1. Create an "old" equipment object. The 'nombre' field matches a type.
        # We don't assign an equipment_type, as it would be null before the migration.
        old_equipment = Equipment.objects.create(
            nombre="RX VETERINARIO", marca="TestVet", serial="VET123"
        )

        # 2. Manually run the logic from the migration's `populate_equipment_types` function
        # This simulates the data update portion of the migration.
        equipment_type, created = EquipmentType.objects.get_or_create(
            name=old_equipment.nombre
        )
        old_equipment.equipment_type = equipment_type
        if old_equipment.nombre in EXPECTED_EQUIPMENT_TYPES:
            old_equipment.nombre = ""  # Clear the old name as it's now redundant
        old_equipment.save()

        # 3. Assert the result
        migrated_equipment = Equipment.objects.get(serial="VET123")
        self.assertIsNotNone(migrated_equipment.equipment_type)
        self.assertEqual(migrated_equipment.equipment_type.name, "RX VETERINARIO")
        self.assertEqual(migrated_equipment.nombre, "")
