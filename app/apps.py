import logging

from django.apps import AppConfig
from django.apps import apps as global_apps
from django.db.models.signals import post_migrate

logger = logging.getLogger(__name__)

ROLES_PERMISSIONS = {
    "cliente": [
        ("view_report", "report", "app"),
    ],
    "gerente": [
        ("add_user", "user", "app"),
        ("view_user", "user", "app"),
        ("delete_user", "user", "app"),
        ("add_external_user", "user", "app"),
        ("manage_equipment", "equipment", "app"),
        ("view_report", "report", "app"),
        ("change_report", "report", "app"),
        ("add_anotacion", "anotacion", "app"),
    ],
    "director_tecnico": [
        ("manage_equipment", "equipment", "app"),
        ("upload_report", "report", "app"),
        ("view_report", "report", "app"),
        ("change_report", "report", "app"),
        ("approve_report", "report", "app"),
        ("add_anotacion", "anotacion", "app"),
        ("view_user", "user", "app"),
    ],
    "personal_tecnico_apoyo": [
        ("manage_equipment", "equipment", "app"),
        ("upload_report", "report", "app"),
        ("view_report", "report", "app"),
        ("change_report", "report", "app"),
        ("add_anotacion", "anotacion", "app"),
        ("view_user", "user", "app"),
    ],
    "personal_administrativo": [
        ("add_external_user", "user", "app"),
        ("view_user", "user", "app"),
        ("view_report", "report", "app"),
        ("change_report", "report", "app"),
        ("add_anotacion", "anotacion", "app"),
    ],
}


class AppConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "app"

    def ready(self):
        import app.signals  # noqa: F401 # Ensure signals are registered

        post_migrate.connect(self.assign_role_permissions, sender=self)
        logger.info(
            f"Connected assign_role_permissions to post_migrate for app: {self.name}"
        )

    def assign_role_permissions(self, sender, **kwargs):
        if sender.name != "app":
            return

        logger.info(f"Running assign_role_permissions for app: {self.name}")

        GroupModel = global_apps.get_model("auth", "Group")
        PermissionModel = global_apps.get_model("auth", "Permission")

        for role_name, perms_info in ROLES_PERMISSIONS.items():
            group, created = GroupModel.objects.get_or_create(name=role_name)
            if created:
                logger.info(f"post_migrate: Created group '{role_name}'")

            to_assign = []
            for codename, model_lower, app_label in perms_info:
                perms_qs = PermissionModel.objects.filter(
                    codename=codename,
                    content_type__app_label=app_label,
                    content_type__model=model_lower,
                )
                if perms_qs.exists():
                    to_assign.extend(perms_qs)
                else:
                    logger.warning(
                        f"post_migrate: permission '{codename}' not found on "
                        f"{app_label}.{model_lower} for role '{role_name}'"
                    )

            group.permissions.set(to_assign)
            # Simplified logging to address the reported SyntaxError
            status_text = "Assigned" if to_assign else "Cleared"
            permissions_count = len(to_assign)
            preposition = "to" if to_assign else "for"
            log_message = f"post_migrate: {status_text} {permissions_count} permissions {preposition} group '{role_name}'."
            logger.info(log_message)
