# Generated by Django 5.1.1 on 2024-10-03 01:21

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('core', '0004_project_members'),
    ]

    operations = [
        migrations.AddField(
            model_name='projectmembership',
            name='created_at',
            field=models.DateTimeField(default=django.utils.timezone.now),
        ),
    ]
