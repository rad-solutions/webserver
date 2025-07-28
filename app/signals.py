import logging

from django.contrib.auth.models import Group
from django.db.models.signals import m2m_changed
from django.dispatch import receiver
from django.utils import timezone

from .models import Process, Role, RoleChoices, User

logger = logging.getLogger(__name__)


@receiver(m2m_changed, sender=User.roles.through)
def sync_user_roles_to_groups(
    sender, instance, action, reverse, model, pk_set, **kwargs
):
    """Synchronize a User's Roles with Django Groups.

    Assumes that for every Role.name (e.g., 'cliente'), a Group with the same name
    exists or will be created (ideally by a data migration).
    """
    if not isinstance(instance, User):
        # This signal is for User.roles, so instance should be a User.
        return

    if action == "post_add":
        for role_pk in pk_set:
            try:
                role = Role.objects.get(pk=role_pk)
                # Use role.name (the value like "cliente") for group name
                group, created = Group.objects.get_or_create(name=role.name)
                instance.groups.add(group)
                if created:
                    # It's better if groups are pre-created by a migration.
                    logger.warning(
                        f"Group '{group.name}' was created by signal for role '{role.name}' while adding user '{instance.username}'. Consider creating all groups via migration."
                    )
                # else:
                #     logger.debug(f"Added user '{instance.username}' to existing group '{group.name}' (linked to role '{role.name}').")
            except Role.DoesNotExist:
                logger.warning(
                    f"Role with pk {role_pk} does not exist. Cannot sync to group for user '{instance.username}'."
                )
            except Exception as e:
                logger.error(
                    f"Error adding user '{instance.username}' to group for role_pk {role_pk}: {e}"
                )

    elif action == "post_remove":
        for role_pk in pk_set:
            try:
                role = Role.objects.get(pk=role_pk)
                group = Group.objects.get(name=role.name)
                instance.groups.remove(group)
                # logger.debug(f"Removed user '{instance.username}' from group '{group.name}' (linked to role '{role.name}').")
            except Role.DoesNotExist:
                logger.warning(
                    f"Role with pk {role_pk} does not exist. Cannot remove user '{instance.username}' from corresponding group."
                )
            except Group.DoesNotExist:
                # This case should ideally not happen if groups are managed correctly.
                logger.warning(
                    f"Group for role '{role.name}' does not exist. Cannot remove user '{instance.username}'."
                )
            except Exception as e:
                logger.error(
                    f"Error removing user '{instance.username}' from group for role_pk {role_pk}: {e}"
                )

    elif action == "post_clear":
        # When roles are cleared, instance.roles.all() will be empty *after* the clear.
        # We need to know which roles *were* associated to remove the user from corresponding groups.
        # The `pk_set` for `post_clear` is not available in all Django versions or scenarios reliably
        # in the same way as `pre_clear`.
        # A robust way is to iterate through all groups that could have been derived from a Role
        # and remove the user from them if they are part of it.
        # This assumes group names directly match Role.name values.

        # Get all possible role names from RoleChoices
        all_role_names = [choice[0] for choice in RoleChoices.choices]

        for role_name_val in all_role_names:
            try:
                group = Group.objects.get(name=role_name_val)
                if instance.groups.filter(
                    pk=group.pk
                ).exists():  # Check if user is in this group
                    instance.groups.remove(group)
                    # logger.debug(f"User '{instance.username}' removed from group '{group.name}' due to roles.clear().")
            except Group.DoesNotExist:
                # If a group corresponding to a potential role name doesn't exist, that's fine.
                pass
            except Exception as e:
                logger.error(
                    f"Error during post_clear for user '{instance.username}', group related to role name '{role_name_val}': {e}"
                )


@receiver(m2m_changed, sender=Process.assigned_to.through)
def process_assigned(sender, instance, action, **kwargs):
    """Set the assignment date when a user is first assigned to a process."""
    if action == "post_add":
        if instance.assigned_to.count() > 0 and instance.fecha_asignacion is None:
            instance.fecha_asignacion = timezone.now()
            instance.save(update_fields=["fecha_asignacion"])
