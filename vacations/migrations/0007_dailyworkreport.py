# Generated for Kalpae daily work reports

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0006_loginattempt'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='DailyWorkReport',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('report_date', models.DateField(verbose_name='fecha')),
                ('machine_number', models.CharField(blank=True, max_length=80, verbose_name='máquina nº')),
                ('truck_number', models.CharField(blank=True, max_length=80, verbose_name='camión nº')),
                ('other_equipment', models.CharField(blank=True, max_length=255, verbose_name='otros')),
                ('client_1', models.CharField(blank=True, max_length=255, verbose_name='cliente 1')),
                ('client_2', models.CharField(blank=True, max_length=255, verbose_name='cliente 2')),
                ('client_3', models.CharField(blank=True, max_length=255, verbose_name='cliente 3')),
                ('client_4', models.CharField(blank=True, max_length=255, verbose_name='cliente 4')),
                ('worksite_1', models.CharField(blank=True, max_length=255, verbose_name='obra 1')),
                ('worksite_2', models.CharField(blank=True, max_length=255, verbose_name='obra 2')),
                ('worksite_3', models.CharField(blank=True, max_length=255, verbose_name='obra 3')),
                ('worksite_4', models.CharField(blank=True, max_length=255, verbose_name='obra 4')),
                ('hours', models.CharField(blank=True, max_length=80, verbose_name='horas')),
                ('trips', models.CharField(blank=True, max_length=80, verbose_name='viajes')),
                ('other_notes', models.CharField(blank=True, max_length=255, verbose_name='otros')),
                ('supplied_material', models.TextField(blank=True, verbose_name='material suministrado')),
                ('work_performed', models.TextField(blank=True, verbose_name='trabajos realizados')),
                ('worker_name', models.CharField(max_length=255, verbose_name='nombre del trabajador')),
                ('signature_name', models.CharField(blank=True, max_length=255, verbose_name='firma')),
                ('pdf', models.FileField(blank=True, null=True, upload_to='daily_work_reports/', verbose_name='PDF generado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='última actualización')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_daily_work_reports', to=settings.AUTH_USER_MODEL, verbose_name='creado por')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='daily_work_reports', to='vacations.employee', verbose_name='trabajador')),
            ],
            options={
                'verbose_name': 'parte personal diario',
                'verbose_name_plural': 'partes personales diarios',
                'ordering': ['-report_date', '-created_at'],
            },
        ),
    ]
