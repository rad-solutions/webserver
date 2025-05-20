from django.db import migrations
import logging

# Assuming your RoleChoices are defined in app.models
# Adjust the import path if your models are elsewhere
from app.models import RoleChoices

logger = logging.getLogger(__name__)


def create_groups_for_roles(apps, schema_editor):
    """Create Django Groups for each RoleChoice if they don't already exist."""
    Role = apps.get_model("app", "Role")  # Get historical Role model
    Group = apps.get_model("auth", "Group")  # This is the correct Group to use

    # Fetch all existing Role objects to get their names
    # This ensures we use the actual 'name' values stored in the DB for Roles
    # (e.g., "cliente", "gerente") rather than the display names.
    existing_roles = Role.objects.all()
    role_names_from_db = {role.name for role in existing_roles}

    # Also consider roles defined in RoleChoices that might not have Role instances yet
    # This is useful if Role instances are created dynamically or later.
    role_names_from_choices = {choice[0] for choice in RoleChoices.choices}

    all_potential_role_names = role_names_from_db.union(role_names_from_choices)

    for role_name in all_potential_role_names:
        group, created = Group.objects.get_or_create(name=role_name)
        if created:
            logger.info(f"Created group: {group.name}")
        # else:
        # logger.info(f'Group {group.name} already exists.')

    # At this point, you would typically also assign default permissions to these groups.
    # For example:
    # try:
    #     gerente_group = Group.objects.get(name=RoleChoices.GERENTE)
    #     # Assuming you have a permission like 'can_approve_reports'
    #     # permission = Permission.objects.get(codename='approve_report', content_type=ContentType.objects.get_for_model(Report))
    #     # gerente_group.permissions.add(permission)
    #     # logger.info(f'Assigned approve_report permission to Gerente group')
    # except Group.DoesNotExist:
    #     logger.warning(f'Group for Gerente not found, cannot assign permissions.')
    # except Permission.DoesNotExist:
    #     logger.warning(f'Permission approve_report not found.')
    # ... and so on for other roles and permissions.


class Migration(migrations.Migration):

    dependencies = [
        (
            "app",
            "0005_alter_equipment_options_alter_report_options_and_more",
        ),  # Adjust to your last relevant migration
        # Add dependency on auth's initial migrations if not already implicitly handled
        # ('auth', '0001_initial'), # Or the latest auth migration that creates Group model
    ]

    operations = [
        migrations.RunPython(create_groups_for_roles),
    ]
