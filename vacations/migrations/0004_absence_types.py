# Generated for Kalpae Gestión de Ausencias - absence types

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0003_pushsubscription'),
    ]

    operations = [
        migrations.AddField(
            model_name='vacationrequest',
            name='absence_type',
            field=models.CharField(
                choices=[
                    ('vacaciones', 'Vacaciones'),
                    ('cita_medica', 'Cita médica'),
                    ('baja_medica', 'Baja médica'),
                    ('ausencia_justificada', 'Ausencia justificada'),
                    ('asuntos_propios', 'Asuntos propios'),
                    ('permiso_retribuido', 'Permiso retribuido'),
                    ('teletrabajo_puntual', 'Teletrabajo puntual'),
                    ('formacion', 'Formación'),
                    ('otros', 'Otros'),
                ],
                default='vacaciones',
                max_length=40,
                verbose_name='tipo de ausencia',
            ),
        ),
        migrations.AddField(
            model_name='vacationrequest',
            name='supporting_document',
            field=models.FileField(
                blank=True,
                null=True,
                upload_to='absence_documents/',
                verbose_name='justificante',
            ),
        ),
    ]
