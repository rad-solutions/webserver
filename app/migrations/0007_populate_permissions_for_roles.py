from django.db import migrations
import logging

logger = logging.getLogger(__name__)


def no_op_forward(apps, schema_editor):
    logger.info(
        "Migration 0007_populate_permissions_for_roles: Forward no-op. Permission assignment moved to post_migrate signal."
    )
    pass


def no_op_backward(apps, schema_editor):
    logger.info(
        "Migration 0007: Backward no-op. Permission assignment reversal "
        "handled by post_migrate or would need specific logic if groups were deleted here."
    )
    pass


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0006_create_role_groups"),
        ("contenttypes", "0002_remove_content_type_name"),
        ("auth", "0012_alter_user_first_name_max_length"),
    ]

    operations = [
        migrations.RunPython(no_op_forward, no_op_backward),
    ]
