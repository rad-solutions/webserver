# Generated by Django 5.2 on 2025-05-15 14:56

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0004_clientprofile_equipment_estado_actual_equipment_sede_and_more"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="equipment",
            options={
                "permissions": [("manage_equipment", "Can create and edit equipment")]
            },
        ),
        migrations.AlterModelOptions(
            name="report",
            options={
                "permissions": [
                    ("upload_report", "Can upload reports"),
                    ("approve_report", "Can approve reports"),
                ]
            },
        ),
        migrations.AlterModelOptions(
            name="user",
            options={
                "permissions": [("add_external_user", "Can add external users only")],
                "verbose_name": "user",
                "verbose_name_plural": "users",
            },
        ),
    ]
