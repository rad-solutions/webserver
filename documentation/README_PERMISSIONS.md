\
# Custom Roles and Permissions System Documentation

This document outlines the custom roles and permissions system implemented in this Django application. It details how application-specific roles are defined, how they integrate with Django's built-in authentication and authorization mechanisms (Groups and Permissions), and the rationale behind the design choices.

## 1. Conceptual Overview

The primary goal is to provide a flexible and maintainable way to manage user access control based on roles that are meaningful to the application's domain, while leveraging Django's robust permission framework.

**Key Concepts:**

*   **Application Roles (`app.models.Role`)**: These are high-level roles defined within the application (e.g., "Cliente", "Gerente", "Director Técnico"). They represent the user's function or standing within the application's context. Users can be assigned multiple such roles.
*   **Django Groups (`django.contrib.auth.models.Group`)**: Django's standard way of categorizing users. In this system, each `app.models.Role` has a corresponding `auth.Group`. For example, an `app.Role` named "gerente" will have an `auth.Group` also named "gerente".
*   **Django Permissions (`django.contrib.auth.models.Permission`)**: Granular permissions automatically created by Django for each model (add, change, delete, view) and any custom permissions defined in model `Meta` classes.
*   **Synchronization**: A mechanism is in place to ensure that when a user is assigned an application `Role`, they are automatically added to the corresponding Django `Group`. Similarly, when a `Role` is removed, they are removed from the `Group`.
*   **Permission Assignment**: Permissions are assigned to Django `Group`s, not directly to users or application `Role`s. This means a user inherits permissions based on the `Group`s they belong to, which in turn are determined by their application `Role`s.

**Why this approach?**

*   **Semantic Roles**: `app.models.Role` provides a clear, domain-specific way to manage user roles in the application logic.
*   **Leveraging Django Auth**: By mapping these roles to Django `Group`s, we can use Django's built-in permission checking mechanisms (`user.has_perm()`, `LoginRequiredMixin`, `PermissionRequiredMixin`, etc.) and the Django Admin interface for managing group permissions.
*   **Decoupling**: Application logic can reason about `app.Role`s, while the underlying access control is handled by Django's `Group` and `Permission` system.

## 2. Core Components

### 2.1. `app/models.py` - Defining Roles and Custom Permissions

*   **`RoleChoices` (Enum)**: Defines the available application roles (e.g., `CLIENTE`, `GERENTE`).
*   **`Role` Model**:
    *   Stores the application-specific roles.
    *   Has a `name` field (e.g., "cliente", "gerente") which is crucial as it's used to link to the `auth.Group` of the same name.
*   **`User` Model (Custom)**:
    *   Subclasses `AbstractUser`.
    *   Includes a ManyToManyField `roles` linking to the `app.models.Role` model. This is how users are assigned their application-specific roles.
*   **Custom Model Permissions (Meta class)**:
    *   Models like `Report`, `Equipment`, etc., can define custom permissions in their `Meta` class. For example:
        ```python
        class Report(models.Model):
            # ... fields ...
            class Meta:
                permissions = [
                    ("approve_report", "Can approve report"),
                    ("upload_report", "Can upload report"),
                    # "view_report" and "change_report" are often standard
                ]
        ```
    *   These custom permissions, along with Django's default ones (add, change, delete, view), are the permissions assigned to `Group`s.
    *   **Important Note on User Permissions**: Since a custom `User` model (`app.User`) is used, permissions like `add_user`, `change_user` are associated with `app.User` (i.e., `app_label='app'`, `model='user'`) and **not** `auth.User` (`app_label='auth'`, `model='user'`). This is critical for the `ROLES_PERMISSIONS` configuration in `app/apps.py`.

### 2.2. `app/signals.py` - Synchronizing User Roles with Django Groups

*   **`sync_user_roles_to_groups` function**: This signal handler is the bridge between `app.Role` and `auth.Group`.
*   **Trigger**: It's connected to the `m2m_changed` signal for the `User.roles` relationship.
*   **Functionality**:
    *   `post_add`: When a `Role` is added to a `User`, the user is added to the `auth.Group` with the same name as the `Role.name`. If the `Group` doesn't exist, it logs a warning (ideally, groups should be pre-created by migrations).
    *   `post_remove`: When a `Role` is removed from a `User`, the user is removed from the corresponding `auth.Group`.
    *   `post_clear`: When all `Role`s are cleared from a `User`, the user is removed from all `Group`s that correspond to any of the defined `RoleChoices`.

### 2.3. `app/migrations/0006_create_role_groups.py` - Initial Group Creation

*   **Purpose**: This is a **data migration**. Its primary responsibility is to create `django.contrib.auth.models.Group` instances in the database for each role defined in `app.models.RoleChoices` (or from existing `Role` model instances).
*   **Why a Data Migration?**:
    *   Ensures that the `Group`s exist before any signals or permission assignment logic tries to interact with them.
    *   Makes the setup process idempotent and part of the standard migration flow.
    *   Without this, the `sync_user_roles_to_groups` signal might try to fetch a non-existent group, or the `assign_role_permissions` logic would have to create groups, mixing concerns.

### 2.4. `app/migrations/0007_populate_permissions_for_roles.py` - (No-Op) Permission Population

*   **Original Intent**: This migration was initially designed to assign permissions to the newly created `Group`s.
*   **Current Status**: It has been modified to be a **no-operation (no-op)** migration. The actual logic for assigning permissions has been moved to a `post_migrate` signal handler in `app/apps.py`.
*   **Reason for Change**:
    *   **`ContentType` Availability**: Assigning permissions within a migration can be problematic because `ContentType`s for all models (especially from other apps like `django.contrib.auth`) might not be fully created or available at the exact point the migration runs. This often leads to "ContentType matching query does not exist" errors.
    *   **Robustness**: The `post_migrate` signal fires after all migrations for an app (and its dependencies, if managed correctly) have completed, providing a more stable environment where all models and their `ContentType`s are expected to be in the database.

### 2.5. `app/apps.py` - Assigning Permissions to Groups (Post-Migration)

*   **`AppConfig.ready()` method**:
    *   Connects the `assign_role_permissions` method to the `post_migrate` signal for the `app` application.
*   **`assign_role_permissions` method**: This is where the core logic for assigning permissions to groups resides.
    *   **Trigger**: Executed after Django has finished running migrations for the `app` application.
    *   **`ROLES_PERMISSIONS` Dictionary**: This dictionary, defined in `app/apps.py`, is the source of truth for which permissions each role (and thus, its corresponding `Group`) should have. It's structured like:
        ```python
        ROLES_PERMISSIONS = {
            "gerente": [
                ("add_user", "user", "app"), # Permission for the custom app.User
                ("manage_equipment", "equipment", "app"),
                # ... other permissions ...
            ],
            # ... other roles ...
        }
        ```
        Each tuple is `(codename, model_name_lower, app_label_for_permission)`.
    *   **Logic**:
        1.  It iterates through each role defined in `ROLES_PERMISSIONS`.
        2.  It retrieves or creates the corresponding `auth.Group` (though `0006_create_role_groups.py` should have already created them).
        3.  For each permission specified for that role:
            *   It **directly queries the `Permission` model** using `content_type__app_label` and `content_type__model` (e.g., `Permission.objects.filter(codename='add_user', content_type__app_label='app', content_type__model='user')`).
            *   This direct query method is crucial because it bypasses potential issues with the `ContentType` cache or the order in which `ContentType`s are created, ensuring reliable lookup of permissions, especially for the custom `app.User` model.
        4.  It then assigns the collected set of `Permission` objects to the `Group.permissions` ManyToManyField.
    *   **Why `post_migrate`?**:
        *   Ensures all migrations from all installed apps have run.
        *   Guarantees that all `ContentType`s and `Permission` objects (including default Django permissions and custom ones) have been created in the database.
        *   Provides the most reliable point to perform permission assignments that depend on the complete schema and initial data of other apps.

## 3. Summary of Workflow

1.  **Define Roles**: Application roles are defined in `app/models.py` (`RoleChoices`, `Role` model).
2.  **Define Permissions**: Custom permissions are defined in the `Meta` class of relevant models in `app/models.py`.
3.  **Create Groups**: The `0006_create_role_groups` migration creates an `auth.Group` for each application role.
4.  **Assign Permissions to Groups**: The `assign_role_permissions` function in `app/apps.py` (triggered by `post_migrate`) assigns the defined Django permissions to these `auth.Group`s based on the `ROLES_PERMISSIONS` mapping.
5.  **User Role Assignment**: When a `User` is assigned an `app.Role` (e.g., via the admin or programmatically):
    *   The `sync_user_roles_to_groups` signal in `app/signals.py` automatically adds the user to the corresponding `auth.Group`.
6.  **Access Control**: Django's permission system then checks if the user is part of a `Group` that has the required permission.

This system provides a clear separation of concerns while ensuring that application-specific roles are seamlessly integrated with Django's powerful authorization framework.
