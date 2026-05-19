# Generated for Kalpae work orders and feature permissions

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0009_dailyjobplan'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PlatformFeaturePermission',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('can_use_vacations', models.BooleanField(default=True, verbose_name='vacaciones/ausencias')),
                ('can_use_daily_reports', models.BooleanField(default=True, verbose_name='partes personales')),
                ('can_use_customer_delivery_notes', models.BooleanField(default=True, verbose_name='albaranes de cliente')),
                ('can_use_daily_jobs', models.BooleanField(default=True, verbose_name='faena diaria')),
                ('can_use_work_orders', models.BooleanField(default=True, verbose_name='órdenes de trabajo')),
                ('notes', models.TextField(blank=True, verbose_name='observaciones internas')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='última actualización')),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='feature_permissions', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={'verbose_name': 'permiso de funciones de plataforma', 'verbose_name_plural': 'permisos de funciones de plataforma'},
        ),
        migrations.CreateModel(
            name='WorkOrder',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('worker_name', models.CharField(max_length=255, verbose_name='nombre del trabajador')),
                ('vehicle_machine', models.CharField(max_length=255, verbose_name='vehículo o máquina')),
                ('order_type', models.CharField(choices=[('maintenance', 'Mantenimiento'), ('repair', 'Reparación')], max_length=30, verbose_name='tipo')),
                ('task_description', models.TextField(verbose_name='descripción de tarea')),
                ('status', models.CharField(choices=[('open', 'Abierta'), ('closed', 'Cerrada')], default='open', max_length=30, verbose_name='estado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='última actualización')),
                ('closed_at', models.DateTimeField(blank=True, null=True, verbose_name='fecha de cierre')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_work_orders', to=settings.AUTH_USER_MODEL, verbose_name='creada por')),
                ('employee', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='work_orders', to='vacations.employee', verbose_name='trabajador')),
            ],
            options={'verbose_name': 'orden de trabajo', 'verbose_name_plural': 'órdenes de trabajo', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='WorkOrderHourEntry',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('work_date', models.DateField(verbose_name='fecha')),
                ('hours', models.DecimalField(decimal_places=2, max_digits=5, verbose_name='horas')),
                ('notes', models.TextField(blank=True, verbose_name='observaciones')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_work_order_hours', to=settings.AUTH_USER_MODEL, verbose_name='creado por')),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='hour_entries', to='vacations.workorder', verbose_name='orden de trabajo')),
            ],
            options={'verbose_name': 'hora de orden de trabajo', 'verbose_name_plural': 'horas de órdenes de trabajo', 'ordering': ['-work_date', '-created_at']},
        ),
        migrations.CreateModel(
            name='WorkOrderReceipt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('receipt_file', models.FileField(upload_to='work_order_receipts/%Y/%m/', verbose_name='foto/PDF de albarán o ticket')),
                ('receipt_date', models.DateField(blank=True, null=True, verbose_name='fecha del albarán/ticket')),
                ('supplier', models.CharField(blank=True, max_length=255, verbose_name='proveedor/taller')),
                ('receipt_number', models.CharField(blank=True, max_length=120, verbose_name='número de albarán/ticket')),
                ('amount', models.DecimalField(blank=True, decimal_places=2, max_digits=10, null=True, verbose_name='importe')),
                ('description', models.TextField(blank=True, verbose_name='descripción')),
                ('uploaded_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha de subida')),
                ('uploaded_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='uploaded_work_order_receipts', to=settings.AUTH_USER_MODEL, verbose_name='subido por')),
                ('work_order', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='receipts', to='vacations.workorder', verbose_name='orden de trabajo')),
            ],
            options={'verbose_name': 'albarán/ticket de orden de trabajo', 'verbose_name_plural': 'albaranes/tickets de órdenes de trabajo', 'ordering': ['-uploaded_at']},
        ),
    ]
