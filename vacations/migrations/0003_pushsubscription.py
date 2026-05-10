# Generated for Kalpae PWA push notifications

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vacations', '0002_employee_user'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PushSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('endpoint', models.URLField(max_length=1000, unique=True)),
                ('p256dh', models.TextField()),
                ('auth', models.TextField()),
                ('user_agent', models.TextField(blank=True)),
                ('is_active', models.BooleanField(default=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='push_subscriptions', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'verbose_name': 'suscripción push',
                'verbose_name_plural': 'suscripciones push',
                'ordering': ['-updated_at'],
            },
        ),
    ]
