# Generated for Kalpae daily job planning

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0008_customerdeliverynote'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyJobPlan',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('plan_date', models.DateField(unique=True, verbose_name='fecha de faena')),
                ('title', models.CharField(blank=True, max_length=255, verbose_name='título')),
                ('notes', models.TextField(blank=True, verbose_name='notas generales')),
                ('is_published', models.BooleanField(default=False, verbose_name='publicada para trabajadores')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='última actualización')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_daily_job_plans', to=settings.AUTH_USER_MODEL, verbose_name='creada por')),
            ],
            options={'verbose_name': 'faena diaria', 'verbose_name_plural': 'faenas diarias', 'ordering': ['-plan_date']},
        ),
        migrations.CreateModel(
            name='DailyJobAssignment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('category', models.CharField(choices=[('work', 'Trabajo/obra'), ('maintenance', 'Mantenimiento'), ('workshop', 'Taller/ITV'), ('training', 'Formación'), ('stopped', 'Parado'), ('subcontracted', 'Subcontratado/alquilado'), ('other', 'Varios')], default='work', max_length=30, verbose_name='tipo')),
                ('client', models.CharField(blank=True, max_length=255, verbose_name='cliente')),
                ('worksite', models.CharField(blank=True, max_length=255, verbose_name='obra/zona')),
                ('machine', models.CharField(blank=True, max_length=255, verbose_name='máquina')),
                ('truck', models.CharField(blank=True, max_length=255, verbose_name='camión')),
                ('worker_name', models.CharField(blank=True, max_length=255, verbose_name='nombre del trabajador')),
                ('hours', models.CharField(blank=True, max_length=80, verbose_name='horas previstas')),
                ('trips', models.CharField(blank=True, max_length=80, verbose_name='viajes previstos')),
                ('notes', models.TextField(blank=True, verbose_name='observaciones')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='orden')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='última actualización')),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='daily_job_assignments', to='vacations.employee', verbose_name='trabajador')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='assignments', to='vacations.dailyjobplan', verbose_name='faena')),
            ],
            options={'verbose_name': 'línea de faena', 'verbose_name_plural': 'líneas de faena', 'ordering': ['sort_order', 'client', 'worksite', 'machine', 'truck', 'worker_name']},
        ),
        migrations.CreateModel(
            name='DailyJobStatusEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('status_type', models.CharField(choices=[('vacation', 'Vacaciones'), ('personal_leave', 'Asuntos propios'), ('sick_leave', 'Baja médica/enfermo'), ('medical_check', 'Reconocimiento'), ('maintenance', 'Mantenimiento'), ('workshop', 'Taller/ITV'), ('training', 'Formación'), ('stopped', 'Parado'), ('subcontracted', 'Subcontratado/alquilado'), ('various', 'Varios')], max_length=40, verbose_name='estado')),
                ('text', models.TextField(verbose_name='detalle')),
                ('sort_order', models.PositiveIntegerField(default=0, verbose_name='orden')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='última actualización')),
                ('plan', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='status_entries', to='vacations.dailyjobplan', verbose_name='faena')),
            ],
            options={'verbose_name': 'estado de faena', 'verbose_name_plural': 'estados de faena', 'ordering': ['status_type', 'sort_order', 'text']},
        ),
    ]
