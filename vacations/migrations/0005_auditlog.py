# Generated for Kalpae security hardening - audit log

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0004_absence_types'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AuditLog',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('action', models.CharField(max_length=80, verbose_name='acción')),
                ('model_name', models.CharField(blank=True, max_length=120, verbose_name='modelo')),
                ('object_id', models.CharField(blank=True, max_length=120, verbose_name='ID objeto')),
                ('object_repr', models.CharField(blank=True, max_length=255, verbose_name='objeto')),
                ('metadata', models.JSONField(blank=True, default=dict, verbose_name='metadatos')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('user_agent', models.TextField(blank=True, verbose_name='user agent')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha')),
                ('actor', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='audit_logs', to=settings.AUTH_USER_MODEL, verbose_name='usuario')),
            ],
            options={
                'verbose_name': 'registro de auditoría',
                'verbose_name_plural': 'registros de auditoría',
                'ordering': ['-created_at'],
            },
        ),
    ]
