# Generated manually for the initial vacation platform schema.
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):
    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='Employee',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('first_name', models.CharField(max_length=120, verbose_name='nombre')),
                ('last_name', models.CharField(max_length=160, verbose_name='apellidos')),
                ('national_id', models.CharField(blank=True, max_length=20, verbose_name='DNI/NIE')),
                ('email', models.EmailField(blank=True, max_length=254, verbose_name='email')),
                ('department', models.CharField(blank=True, max_length=120, verbose_name='departamento')),
                ('position', models.CharField(blank=True, max_length=120, verbose_name='puesto')),
                ('annual_days', models.PositiveSmallIntegerField(default=22, verbose_name='días anuales')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
            ],
            options={'verbose_name': 'trabajador', 'verbose_name_plural': 'trabajadores', 'ordering': ['last_name', 'first_name']},
        ),
        migrations.CreateModel(
            name='VacationRequest',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateField(verbose_name='fecha de inicio')),
                ('end_date', models.DateField(verbose_name='fecha de fin')),
                ('requested_days', models.DecimalField(decimal_places=1, max_digits=5, verbose_name='días solicitados')),
                ('notes', models.TextField(blank=True, verbose_name='observaciones del trabajador')),
                ('status', models.CharField(choices=[('draft', 'Borrador'), ('pending', 'Pendiente de dirección'), ('approved', 'Aprobada'), ('rejected', 'Denegada'), ('cancelled', 'Cancelada')], default='pending', max_length=20, verbose_name='estado')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('request_pdf', models.FileField(blank=True, upload_to='vacation_documents/', verbose_name='PDF solicitud')),
                ('created_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='created_vacation_requests', to=settings.AUTH_USER_MODEL)),
                ('employee', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='requests', to='vacations.employee', verbose_name='trabajador')),
            ],
            options={'verbose_name': 'solicitud de vacaciones', 'verbose_name_plural': 'solicitudes de vacaciones', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='VacationDecision',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('decision', models.CharField(choices=[('approved', 'Aprobada'), ('rejected', 'Denegada')], max_length=20, verbose_name='decisión')),
                ('decided_at', models.DateTimeField(auto_now_add=True)),
                ('company_notes', models.TextField(blank=True, verbose_name='observaciones de dirección')),
                ('decision_pdf', models.FileField(blank=True, upload_to='vacation_documents/', verbose_name='PDF decisión')),
                ('decided_by', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='vacation_decisions', to=settings.AUTH_USER_MODEL)),
                ('request', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, related_name='decision', to='vacations.vacationrequest', verbose_name='solicitud')),
            ],
            options={'verbose_name': 'decisión de vacaciones', 'verbose_name_plural': 'decisiones de vacaciones', 'ordering': ['-decided_at']},
        ),
    ]
