# Adds optional user-to-employee binding for role-based access.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddField(
            model_name='employee',
            name='user',
            field=models.OneToOneField(
                blank=True,
                help_text='Opcional. Permite que el trabajador acceda solo a sus propias solicitudes.',
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                related_name='employee_profile',
                to=settings.AUTH_USER_MODEL,
                verbose_name='usuario vinculado',
            ),
        ),
    ]
