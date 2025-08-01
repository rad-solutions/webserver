# Generated by Django 5.2 on 2025-07-30 14:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app", "0032_process_fecha_asignacion"),
    ]

    operations = [
        migrations.AlterField(
            model_name="checklistitemdefinition",
            name="process_type",
            field=models.CharField(
                choices=[
                    ("calculo_blindajes", "Cálculo de Blindajes"),
                    ("control_calidad", "Control de Calidad"),
                    ("estudio_ambiental", "Estudio Ambiental"),
                    ("niveles_de_referencia", "Niveles de Referencia"),
                    ("asesoria", "Asesoría"),
                    ("otro", "Otro"),
                ],
                max_length=25,
                verbose_name="Tipo de Proceso",
            ),
        ),
        migrations.AlterField(
            model_name="process",
            name="process_type",
            field=models.CharField(
                choices=[
                    ("calculo_blindajes", "Cálculo de Blindajes"),
                    ("control_calidad", "Control de Calidad"),
                    ("estudio_ambiental", "Estudio Ambiental"),
                    ("niveles_de_referencia", "Niveles de Referencia"),
                    ("asesoria", "Asesoría"),
                    ("otro", "Otro"),
                ],
                default="otro",
                max_length=25,
            ),
        ),
    ]
