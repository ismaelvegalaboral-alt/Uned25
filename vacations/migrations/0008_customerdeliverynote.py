# Generated for Kalpae customer delivery notes

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0007_dailyworkreport'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='CustomerDeliveryNote',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('note_date', models.DateField(verbose_name='fecha')),
                ('customer_name', models.CharField(max_length=255, verbose_name='cliente')),
                ('phone', models.CharField(blank=True, max_length=80, verbose_name='teléfono')),
                ('tax_id', models.CharField(blank=True, max_length=80, verbose_name='CIF/NIF')),
                ('worksite', models.CharField(blank=True, max_length=255, verbose_name='obra')),
                ('address', models.CharField(blank=True, max_length=255, verbose_name='dirección')),
                ('machine_1', models.CharField(blank=True, max_length=255, verbose_name='máquina 1')),
                ('machine_1_hours', models.CharField(blank=True, max_length=80, verbose_name='horas máquina 1')),
                ('machine_2', models.CharField(blank=True, max_length=255, verbose_name='máquina 2')),
                ('machine_2_hours', models.CharField(blank=True, max_length=80, verbose_name='horas máquina 2')),
                ('truck_1', models.CharField(blank=True, max_length=255, verbose_name='camión 1')),
                ('truck_1_hours', models.CharField(blank=True, max_length=80, verbose_name='horas camión 1')),
                ('truck_1_trips', models.CharField(blank=True, max_length=80, verbose_name='viajes camión 1')),
                ('truck_2', models.CharField(blank=True, max_length=255, verbose_name='camión 2')),
                ('truck_2_hours', models.CharField(blank=True, max_length=80, verbose_name='horas camión 2')),
                ('truck_2_trips', models.CharField(blank=True, max_length=80, verbose_name='viajes camión 2')),
                ('truck_3', models.CharField(blank=True, max_length=255, verbose_name='camión 3')),
                ('truck_3_hours', models.CharField(blank=True, max_length=80, verbose_name='horas camión 3')),
                ('truck_3_trips', models.CharField(blank=True, max_length=80, verbose_name='viajes camión 3')),
                ('truck_4', models.CharField(blank=True, max_length=255, verbose_name='camión 4')),
                ('truck_4_hours', models.CharField(blank=True, max_length=80, verbose_name='horas camión 4')),
                ('truck_4_trips', models.CharField(blank=True, max_length=80, verbose_name='viajes camión 4')),
                ('truck_5', models.CharField(blank=True, max_length=255, verbose_name='camión 5')),
                ('truck_5_hours', models.CharField(blank=True, max_length=80, verbose_name='horas camión 5')),
                ('truck_5_trips', models.CharField(blank=True, max_length=80, verbose_name='viajes camión 5')),
                ('work_description', models.TextField(blank=True, verbose_name='descripción de trabajos realizados')),
                ('materials', models.TextField(blank=True, verbose_name='otros conceptos o materiales')),
                ('observations', models.TextField(blank=True, verbose_name='observaciones')),
                ('received_by', models.CharField(blank=True, max_length=255, verbose_name='recibí conforme')),
                ('signature_image', models.FileField(blank=True, null=True, upload_to='customer_delivery_notes/signatures/', verbose_name='firma cliente')),
                ('pdf', models.FileField(blank=True, null=True, upload_to='customer_delivery_notes/', verbose_name='PDF generado')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha de creación')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='última actualización')),
                ('created_by', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_customer_delivery_notes', to=settings.AUTH_USER_MODEL, verbose_name='creado por')),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='customer_delivery_notes', to='vacations.employee', verbose_name='trabajador')),
            ],
            options={
                'verbose_name': 'albarán de cliente',
                'verbose_name_plural': 'albaranes de cliente',
                'ordering': ['-note_date', '-created_at'],
            },
        ),
    ]
