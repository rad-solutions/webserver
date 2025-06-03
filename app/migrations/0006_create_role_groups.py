from django.db import migrations
import logging
from app.models import RoleChoices

logger = logging.getLogger(__name__)


def create_groups_for_roles(apps, schema_editor):
    """Create Django Groups for each RoleChoice if they don't already exist."""
    Role = apps.get_model("app", "Role")
    Group = apps.get_model("auth", "Group")

    existing_roles = Role.objects.all()
    role_names_from_db = {role.name for role in existing_roles}

    role_names_from_choices = {choice[0] for choice in RoleChoices.choices}

    all_potential_role_names = role_names_from_db.union(role_names_from_choices)

    for role_name in all_potential_role_names:
        group, created = Group.objects.get_or_create(name=role_name)
        if created:
            logger.info(f"Created group: {group.name}")
        # else:
        # logger.info(f'Group {group.name} already exists.')


class Migration(migrations.Migration):

    dependencies = [
        (
            "app",
            "0005_alter_equipment_options_alter_report_options_and_more",
        ),
    ]

    operations = [
        migrations.RunPython(create_groups_for_roles),
    ]
