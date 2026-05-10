# Generated for Kalpae login rate limiting

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0005_auditlog'),
    ]

    operations = [
        migrations.CreateModel(
            name='LoginAttempt',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('ip_address', models.GenericIPAddressField(blank=True, null=True, verbose_name='IP')),
                ('username', models.CharField(blank=True, max_length=255, verbose_name='usuario/email')),
                ('path', models.CharField(blank=True, max_length=255, verbose_name='ruta')),
                ('success', models.BooleanField(default=False, verbose_name='correcto')),
                ('blocked', models.BooleanField(default=False, verbose_name='bloqueado')),
                ('user_agent', models.TextField(blank=True, verbose_name='user agent')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='fecha')),
            ],
            options={
                'verbose_name': 'intento de login',
                'verbose_name_plural': 'intentos de login',
                'ordering': ['-created_at'],
                'indexes': [
                    models.Index(fields=['ip_address', 'created_at'], name='vacations_l_ip_addr_57fa7d_idx'),
                    models.Index(fields=['username', 'created_at'], name='vacations_l_usernam_4243ef_idx'),
                    models.Index(fields=['success', 'created_at'], name='vacations_l_success_202a9a_idx'),
                ],
            },
        ),
    ]
